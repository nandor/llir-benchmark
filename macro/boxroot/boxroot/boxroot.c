/* {{{ Includes */

// This is emacs folding-mode

#include <assert.h>
#include <errno.h>
#include <limits.h>
#if defined(ENABLE_BOXROOT_MUTEX) && (ENABLE_BOXROOT_MUTEX == 1)
#include <pthread.h>
#endif
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define CAML_NAME_SPACE
#define CAML_INTERNALS

#include "boxroot.h"
#include <caml/roots.h>
#include <caml/minor_gc.h>
#include <caml/major_gc.h>
#include <caml/compact.h>

#if defined(_POSIX_TIMERS) && defined(_POSIX_MONOTONIC_CLOCK)
#define POSIX_CLOCK
#include <time.h>
#endif

/* }}} */

/* {{{ Parameters */

/* Log of the size of the pools (12 = 4KB, an OS page).
   Recommended: 14. */
#define POOL_LOG_SIZE 14
/* Check integrity of pool structure after each scan, and print
   additional statistics? (slow)
   This can also be enabled by defining the macro BOXROOT_DEBUG.
   Recommended: 0. */
#define DEBUG 0

/* }}} */

/* {{{ Setup */

#ifdef BOXROOT_DEBUG
#undef DEBUG
#define DEBUG 1
#endif

#define POOL_SIZE ((size_t)1 << POOL_LOG_SIZE)
#define POOL_ALIGNMENT POOL_SIZE

/* }}} */

/* {{{ Data types */

typedef enum class {
  YOUNG,
  OLD,
  UNTRACKED
} class;

typedef void * slot;

struct header {
  struct pool *prev;
  struct pool *next;
  slot *free_list;
  int alloc_count;
  class class;
};

static_assert(POOL_SIZE / sizeof(slot) <= INT_MAX, "pool size too large");

#define POOL_ROOTS_CAPACITY                                 \
  ((int)((POOL_SIZE - sizeof(struct header)) / sizeof(slot)))

typedef struct pool {
  struct header hd;
  /* Occupied slots are OCaml values.
     Unoccupied slots are a pointer to the next slot in the free list,
     or to pool itself, denoting the empty free list. */
  slot roots[POOL_ROOTS_CAPACITY];
} pool;

static_assert(sizeof(pool) == POOL_SIZE, "bad pool size");

/* }}} */

/* {{{ Globals */

/* Global pool rings. */
static struct {
/* Pools of old values: contains only roots pointing to the major
   heap. Scanned at the start of major collection. */
  /* Full or almost. Not considered for allocation. */
  pool *old_full;
  /* Next considered for allocation. */
  pool *old_available;
  /* Pools with lots of available space, considered in priority for
     recycling into a young pool.*/
  pool *old_low;

/* Pools of young values: contains roots pointing to the major or to
   the minor heap. Scanned at the start of minor and major
   collection. */
  /* Next considered for allocation. */
  pool *young_available;
  /* Full or almost. Not considered for allocation. */
  pool *young_full;

/* Pools containing no root: not scanned.

   We could free these pools immediately, but this could lead to
   stuttering behavior for workloads that regularly come back to
   0 boxroots alive. Instead we wait for the next major slice to free
   empty pools.
 */
  pool *free;
} pools;

static pool ** const global_rings[] =
  { &pools.old_full, &pools.old_available, &pools.old_low,
    &pools.young_available, &pools.young_full,
    &pools.free,
    NULL };

static const class global_ring_classes[] =
  { OLD, OLD, OLD,
    YOUNG, YOUNG,
    UNTRACKED };

/* Iterate on all global rings.
   [global_ring]: a variable of type [pool**].
   [cl]: a variable of type [class].
   [action]: an expression that can refer to global_ring and cl.
*/
#define FOREACH_GLOBAL_RING(global_ring, cl, action) do {               \
    pool ** const *b__st = &global_rings[0];                            \
    for (pool ** const *b__i = b__st; *b__i != NULL; b__i++) {          \
      pool **global_ring = *b__i;                                       \
      class cl = global_ring_classes[b__i - b__st];                     \
      action;                                                           \
    }                                                                   \
  } while (0)

#if defined(ENABLE_BOXROOT_MUTEX) && (ENABLE_BOXROOT_MUTEX == 1)
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
#define CRITICAL_SECTION_BEGIN() pthread_mutex_lock(&mutex)
#define CRITICAL_SECTION_END() pthread_mutex_unlock(&mutex)
#else
#define CRITICAL_SECTION_BEGIN()
#define CRITICAL_SECTION_END()
#endif

struct stats {
  int minor_collections;
  int major_collections;
  int total_create;
  int total_delete;
  int total_modify;
  long long total_scanning_work_minor;
  long long total_scanning_work_major;
  int64_t total_minor_time;
  int64_t total_major_time;
  int64_t peak_minor_time;
  int64_t peak_major_time;
  int total_alloced_pools;
  int total_freed_pools;
  int live_pools; // number of tracked pools
  int peak_pools; // max live pools at any time
  int ring_operations; // Number of times hd.next is mutated
  long long is_young; // number of times is_young was called
  long long young_hit; // number of times a young value was encountered
                       // during scanning
  long long get_pool_header; // number of times get_pool_header was called
  long long is_pool_member; // number of times is_pool_member was called
  long long is_empty_free_list; // number of times is_empty_free_list was called
};

static struct stats stats;

/* }}} */

/* {{{ Tests in the hot path */

// hot path
static inline pool * get_pool_header(slot *v)
{
  if (DEBUG) ++stats.get_pool_header;
  return (pool *)((uintptr_t)v & ~((uintptr_t)POOL_SIZE - 1));
}

// Return true iff v shares the same msbs as p and is not an
// immediate.
// hot path
static inline int is_pool_member(slot v, pool *p)
{
  if (DEBUG) ++stats.is_pool_member;
  return (uintptr_t)p == ((uintptr_t)v & ~((uintptr_t)POOL_SIZE - 2));
}

// hot path
static inline int is_empty_free_list(slot *v, pool *p)
{
  if (DEBUG) ++stats.is_empty_free_list;
  return (v == (slot *)p);
}

// hot path
static inline int is_young_block(value v)
{
  if (DEBUG) ++stats.is_young;
  return Is_block(v) && Is_young(v);
}

/* }}} */

/* {{{ Platform-specific allocation */

static void * alloc_uninitialised_pool()
{
  void *p = NULL;
  // TODO: portability?
  // Win32: p = _aligned_malloc(size, alignment);
  int err = posix_memalign(&p, POOL_ALIGNMENT, POOL_SIZE);
  assert(err != EINVAL);
  if (err == ENOMEM) return NULL;
  assert(p != NULL);
  ++stats.total_alloced_pools;
  return p;
}

static void free_pool(pool *p) {
    // Win32: _aligned_free(p);
    free(p);
}

/* }}} */

/* {{{ Ring operations */

static void ring_link(pool *p, pool *q)
{
  p->hd.next = q;
  q->hd.prev = p;
  ++stats.ring_operations;
}

static void validate_pool(pool*);

// insert the ring [source] at the back of [*target].
static void ring_push_back(pool *source, pool **target)
{
  if (source == NULL) return;
  if (*target == NULL) {
    *target = source;
    if (DEBUG) {
      FOREACH_GLOBAL_RING(global, class, {
          assert(target != global || source->hd.class == class);
        });
    }
  } else {
    assert((*target)->hd.class == source->hd.class);
    pool *target_last = (*target)->hd.prev;
    pool *source_last = source->hd.prev;
    ring_link(target_last, source);
    ring_link(source_last, *target);
  }
}

// remove the first element from [*target] and return it
static pool * ring_pop(pool **target)
{
  pool *front = *target;
  assert(front);
  if (front->hd.next == front) {
    *target = NULL;
    return front;
  }
  ring_link(front->hd.prev, front->hd.next);
  *target = front->hd.next;
  ring_link(front, front);
  return front;
}

/* }}} */

/* {{{ Pool management */

static pool * get_uninitialised_pool()
{
  pool *p = alloc_uninitialised_pool();
  if (p == NULL) return NULL;
  ring_link(p, p);
  p->hd.free_list = NULL;
  p->hd.alloc_count = 0;
  p->hd.class = UNTRACKED;
  return p;
}

// the empty free-list for a pool p is denoted by a pointer to the pool itself
// (NULL could be a valid value for an element slot)
static inline slot empty_free_list(pool *p) {
  return (slot)p;
}

static inline int is_full_pool(pool *p)
{
  return is_empty_free_list(p->hd.free_list, p);
}

static pool * get_empty_pool()
{
  ++stats.live_pools;
  if (stats.live_pools > stats.peak_pools) stats.peak_pools = stats.live_pools;
  pool *out = get_uninitialised_pool();

  if (out == NULL) return NULL;

  out->roots[POOL_ROOTS_CAPACITY - 1] = empty_free_list(out);
  for (slot *s = out->roots + POOL_ROOTS_CAPACITY - 2; s >= out->roots; --s) {
    *s = (slot)(s + 1);
  }
  out->hd.free_list = out->roots;
  return out;
}

static void pool_remove(pool *p)
{
  pool *old = ring_pop(&p);
  FOREACH_GLOBAL_RING(global, cl, {
      if (*global == old) *global = p;
    });
}

static void free_pool_ring(pool **ring) {
  while (*ring != NULL) {
      pool *p = ring_pop(ring);
      free_pool(p);
  }
}

static void free_all_pools()
{
  FOREACH_GLOBAL_RING(global, cl, {
    free_pool_ring(global);
  });
}

/* }}} */

/* {{{ Pool class management */

/* Take the slow path on deallocation every DEALLOC_THRESHOLD_SIZE
   deallocations. */
#define DEALLOC_THRESHOLD_SIZE_LOG 4 // 16
#define DEALLOC_THRESHOLD_SIZE ((int)1 << DEALLOC_THRESHOLD_SIZE_LOG)
/* The pool is divided in NUM_DEALLOC_THRESHOLD parts of equal size
   DEALLOC_THRESHOLD_SIZE. */
#define NUM_DEALLOC_THRESHOLD (POOL_SIZE / (DEALLOC_THRESHOLD_SIZE * sizeof(slot)))
/* Old pools become candidate for young allocation below
   LOW_COUNT_THRESHOLD / NUM_DEALLOC_THRESHOLD occupancy. This tries
   to guarantee that minor scanning hits a good proportion of young
   values. */
#define LOW_COUNT_THRESHOLD (NUM_DEALLOC_THRESHOLD / 2)
/* Pools become candidate for allocation below HIGH_COUNT_THRESHOLD /
   NUM_DEALLOC_THRESHOLD occupancy. */
#define HIGH_COUNT_THRESHOLD (NUM_DEALLOC_THRESHOLD - 1)

static_assert(0 < LOW_COUNT_THRESHOLD, "");
static_assert(LOW_COUNT_THRESHOLD < HIGH_COUNT_THRESHOLD, "");
static_assert(HIGH_COUNT_THRESHOLD < NUM_DEALLOC_THRESHOLD, "");
static_assert(1 + HIGH_COUNT_THRESHOLD * DEALLOC_THRESHOLD_SIZE
              < POOL_ROOTS_CAPACITY, "HIGH_COUNT_THRESHOLD too high");

// hot path
static inline int is_alloc_threshold(int alloc_count)
{
  return (alloc_count & (DEALLOC_THRESHOLD_SIZE - 1)) == 0;
}

typedef enum occupancy {
  EMPTY,
  LOW,
  HIGH,
  QUASI_FULL,
  NO_CHANGE
} occupancy;

static int get_threshold(int alloc_count)
{
  return 1 + (alloc_count - 1) / DEALLOC_THRESHOLD_SIZE;
}

static occupancy promotion_occupancy(pool *p)
{
  int threshold = get_threshold(p->hd.alloc_count);
  if (threshold == 0) return EMPTY;
  if (threshold <= LOW_COUNT_THRESHOLD) return LOW;
  if (threshold <= HIGH_COUNT_THRESHOLD) return HIGH;
  return QUASI_FULL;
}

static occupancy demotion_occupancy(pool *p)
{
  assert(is_alloc_threshold(p->hd.alloc_count));
  int threshold = get_threshold(p->hd.alloc_count);
  if (threshold == 0) return EMPTY;
  if (threshold == LOW_COUNT_THRESHOLD && p->hd.class == OLD) return LOW;
  if (threshold == HIGH_COUNT_THRESHOLD) return HIGH;
  return NO_CHANGE;
}

static void pool_reclassify(pool *p, occupancy occ)
{
  assert(occ != NO_CHANGE);
  assert(p->hd.next == p);
  class cl = p->hd.class;
  assert((cl == UNTRACKED) == (occ == EMPTY));
  int is_young = cl == YOUNG;
  pool **target = NULL;
  switch (occ) {
  case EMPTY:
    assert(p->hd.alloc_count == 0);
    target = &pools.free;
    break;
  case LOW:
    target = is_young ? &pools.young_available : &pools.old_low;
    break;
  case HIGH:
    target = is_young ? &pools.young_available : &pools.old_available;
    break;
  case QUASI_FULL:
    target = is_young ? &pools.young_full : &pools.old_full;
    break;
  }
  // Add at the end instead of in front, since pools which have been
  // there longer might be better choices for selection.
  ring_push_back(p, target);
}

static void try_demote_pool(pool *p)
{
  occupancy occ = demotion_occupancy(p);
  if (occ == NO_CHANGE) return;
  if (occ != EMPTY &&
      (p == pools.young_available || p == pools.old_available)) {
    // Ignore the pool currently used for allocation unless it is empty.
    return;
  }
  pool_remove(p);
  if (occ == EMPTY) p->hd.class = UNTRACKED;
  pool_reclassify(p, occ);
}

// Find an available pool for the class (young or old), ensure it is a
// the start of the corresponding ring of available pools, and return
// the pool. Return NULL if none was found and the allocation of a new
// one failed.
static pool * find_available_pool(int for_young)
{
  pool **target = for_young ? &pools.young_available : &pools.old_available;
  // Reclassify the first pool if it is full
  if (*target != NULL && is_full_pool(*target)) {
      pool *full = ring_pop(target);
      assert(promotion_occupancy(full) == QUASI_FULL);
      assert(for_young == (YOUNG == full->hd.class));
      pool_reclassify(full, QUASI_FULL);
  }
  // Note: we only ever allocate from the the first pool of each ring,
  // so there is at most one full pool in front of the ring. We just
  // reclassified it with the test above, so the next pool
  // (if it exists) cannot be full.
  if (*target != NULL) {
    assert(!is_full_pool(*target));
    return *target;
  }
  pool *new_pool = NULL;
  if (pools.old_low != NULL) {
    // YOUNG: We prefer to use an old pool which is not too full. We try to
    // guarantee a good young-to-old ratio during minor scanning.
    // OLD: We reserve the less full pools for re-use as young pools, but
    // we did what we could, so take a less full one anyway.
    new_pool = ring_pop(&pools.old_low);
    // Do not bother with quasi-full pools.
  } else if (pools.free != NULL) {
    new_pool = ring_pop(&pools.free);
  } else {
    new_pool = get_empty_pool();
  }
  if (new_pool == NULL) return NULL;
  new_pool->hd.class = for_young ? YOUNG : OLD;
  assert(*target == NULL);
  *target = new_pool;
  return new_pool;
}

static void promote_young_pools()
{
  // Promote full pools
  pool *start = pools.young_full;
  if (start != NULL) {
    pool *p = start;
    do {
      p->hd.class = OLD;
      p = p->hd.next;
    } while (p != start);
    ring_push_back(pools.young_full, &pools.old_full);
    pools.young_full = NULL;
  }
  // Promote available pools
  pool *head_young = pools.young_available;
  while (pools.young_available != NULL) {
    pool *p = ring_pop(&pools.young_available);
    occupancy occ = promotion_occupancy(p);
    assert(occ != NO_CHANGE);
    // A young pool can be empty if it has not been allocated
    // into yet, or if it is the last available young pool.
    p->hd.class = (occ == EMPTY) ? UNTRACKED : OLD;
    pool_reclassify(p, occ);
  }
  // For very-low-latency applications: A program that does not use
  // any boxroot should not have to pay the cost of scanning any pool.
  assert(pools.young_available == NULL);
  // Heuristic: if a young pool has just been allocated, it is better
  // if it is the first one to be considered next time a young boxroot
  // allocation takes place.
  if (head_young != NULL && promotion_occupancy(head_young) == LOW) {
    pools.old_low = head_young;
  }
}

/* }}} */

/* {{{ Allocation, deallocation */

#if defined(__GNUC__)
#define LIKELY(a) __builtin_expect(!!(a),1)
#define UNLIKELY(a) __builtin_expect(!!(a),0)
#else
#define LIKELY(a) (a)
#define UNLIKELY(a) (a)
#endif

static slot * alloc_slot_slow(int);

// hot path
static inline slot * alloc_slot(int for_young_block)
{
  pool *p = for_young_block ? pools.young_available : pools.old_available;
  if (LIKELY(p != NULL)) {
    slot *new_root = p->hd.free_list;
    if (LIKELY(!is_empty_free_list(new_root, p))) {
      p->hd.free_list = (slot *)*new_root;
      p->hd.alloc_count++;
      return new_root;
    }
  }
  return alloc_slot_slow(for_young_block);
}

static int setup;

// Place an available pool in front of the ring and allocate from it.
static slot * alloc_slot_slow(int for_young_block)
{
  // We might be here because boxroot is not setup.
  if (!setup) {
    fprintf(stderr, "boxroot is not setup\n");
    return NULL;
  }
  // TODO Latency: bound the number of young roots alloced at each
  // minor collection by scheduling a minor collection.
  pool *p = find_available_pool(for_young_block);
  if (p == NULL) return NULL;
  assert(!is_full_pool(p));
  assert(for_young_block == (p->hd.class == YOUNG));
  return alloc_slot(for_young_block);
}

// hot path
// assumes [is_pool_member(s, p)]
static inline void free_slot(slot *s, pool *p)
{
  *s = (slot)p->hd.free_list;
  p->hd.free_list = s;
  if (DEBUG) assert(p->hd.alloc_count > 0);
  if (UNLIKELY(is_alloc_threshold(--p->hd.alloc_count))) {
    try_demote_pool(p);
  }
}

/* }}} */

/* {{{ Boxroot API implementation */

// hot path
static inline boxroot root_create_classified(value init, int for_young_block)
{
  value *cell = (value *)alloc_slot(for_young_block);
  if (LIKELY(cell != NULL)) *cell = init;
  return (boxroot)cell;
}

// hot path
boxroot boxroot_create(value init)
{
  CRITICAL_SECTION_BEGIN();
  if (DEBUG) ++stats.total_create;
  boxroot br = root_create_classified(init, is_young_block(init));
  CRITICAL_SECTION_END();
  return br;
}

extern value boxroot_get(boxroot root);
extern value const * boxroot_get_ref(boxroot root);

// hot path
void boxroot_delete(boxroot root)
{
  CRITICAL_SECTION_BEGIN();
  slot *s = (slot *)root;
  CAMLassert(s);
  if (DEBUG) ++stats.total_delete;
  free_slot(s, get_pool_header(s));
  CRITICAL_SECTION_END();
}

static void boxroot_reallocate(boxroot *root, pool *p, value new_value)
{
  boxroot new = root_create_classified(new_value, 1);
  if (LIKELY(new != NULL)) {
    free_slot((slot *)*root, p);
    *root = new;
  } else {
    // Better not fail in boxroot_modify. Expensive but fail-safe:
    pool_remove(p);
    p->hd.class = YOUNG;
    ring_push_back(p, &pools.young_available);
  }
}

// hot path
void boxroot_modify(boxroot *root, value new_value)
{
  CRITICAL_SECTION_BEGIN();
  slot *s = (slot *)*root;
  CAMLassert(s);
  if (DEBUG) ++stats.total_modify;
  int is_new_young_block = is_young_block(new_value);
  pool *p;
  if (LIKELY(!is_new_young_block
             || (p = get_pool_header(s))->hd.class == YOUNG)) {
    *(value *)s = new_value;
  } else {
    // We need to reallocate, but this reallocation happens at most once
    // between two minor collections.
    boxroot_reallocate(root, p, new_value);
  }
  CRITICAL_SECTION_END();
}

/* }}} */

/* {{{ Scanning */

static void validate_pool(pool *pool)
{
  if (pool->hd.free_list == NULL) {
    // an unintialised pool
    assert(pool->hd.class == UNTRACKED);
    return;
  }
  // check freelist structure and length
  slot *curr = pool->hd.free_list;
  int pos = 0;
  for (; !is_empty_free_list(curr, pool); curr = (slot*)*curr, pos++)
  {
    assert(pos < POOL_ROOTS_CAPACITY);
    assert(curr >= pool->roots && curr < pool->roots + POOL_ROOTS_CAPACITY);
  }
  assert(pos == POOL_ROOTS_CAPACITY - pool->hd.alloc_count);
  // check count of allocated elements
  int alloc_count = 0;
  for(int i = 0; i < POOL_ROOTS_CAPACITY; i++) {
    slot s = pool->roots[i];
    --stats.is_pool_member;
    if (!is_pool_member(s, pool)) {
      value v = (value)s;
      if (pool->hd.class != YOUNG) assert(!Is_block(v) || !Is_young(v));
      ++alloc_count;
    }
  }
  assert(alloc_count == pool->hd.alloc_count);
}

static void validate_all_pools()
{
  FOREACH_GLOBAL_RING(global, class, {
      pool *start_pool = *global;
      if (start_pool == NULL) continue;
      pool *p = start_pool;
      do {
        assert(p->hd.class == class);
        validate_pool(p);
        assert(p->hd.next != NULL);
        assert(p->hd.next->hd.prev == p);
        assert(p->hd.prev != NULL);
        assert(p->hd.prev->hd.next == p);
        p = p->hd.next;
      } while (p != start_pool);
    });
}

static int in_minor_collection = 0;

// returns the amount of work done
static int scan_pool(scanning_action action, pool *pool)
{
  int allocs_to_find = pool->hd.alloc_count;
  slot *current = pool->roots;
  while (allocs_to_find) {
    // hot path
    slot s = *current;
    if (LIKELY((!is_pool_member(s, pool)))) {
      --allocs_to_find;
      value v = (value)s;
      if (DEBUG && Is_block(v) && Is_young(v)) ++stats.young_hit;
      action(v, (value *)current);
    }
    ++current;
  }
  return current - pool->roots;
}

static int scan_pools(scanning_action action)
{
  int work = 0;
  FOREACH_GLOBAL_RING(global, class, {
      if (class == UNTRACKED || (in_minor_collection && class == OLD))
        continue;
      pool *start_pool = *global;
      if (start_pool == NULL) continue;
      pool *p = start_pool;
      do {
        work += scan_pool(action, p);
        p = p->hd.next;
      } while (p != start_pool);
    });
  return work;
}

static void scan_roots(scanning_action action)
{
  if (DEBUG) validate_all_pools();
  int work = scan_pools(action);
  if (in_minor_collection) {
    promote_young_pools();
    stats.total_scanning_work_minor += work;
  } else {
    stats.total_scanning_work_major += work;
    free_pool_ring(&pools.free);
  }
  if (DEBUG) validate_all_pools();
}

/* }}} */

/* {{{ Statistics */

static int64_t time_counter(void)
{
#if defined(POSIX_CLOCK)
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return (int64_t)t.tv_sec * (int64_t)1000000000 + (int64_t)t.tv_nsec;
#else
  return 0;
#endif
}

// 1=KiB, 2=MiB
static int kib_of_pools(int count, int unit)
{
  int log_per_pool = POOL_LOG_SIZE - unit * 10;
  if (log_per_pool >= 0) return count << log_per_pool;
  /* log_per_pool < 0) */
  return count >> -log_per_pool;
}

static int average(long long total_work, int nb_collections)
{
  if (nb_collections <= 0) return -1;
  // round to nearest
  return (total_work + (nb_collections / 2)) / nb_collections;
}

static int boxroot_used()
{
  FOREACH_GLOBAL_RING (global, class, {
      if (class == UNTRACKED) continue;
      pool *p = *global;
      if (p != NULL && (p->hd.alloc_count != 0 || p->hd.next != p)) {
        return 1;
      }
    });
  return 0;
}

void boxroot_print_stats()
{
  printf("minor collections: %d\n"
         "major collections (and others): %d\n",
         stats.minor_collections,
         stats.major_collections);

  int scanning_work_minor = average(stats.total_scanning_work_minor, stats.minor_collections);
  int scanning_work_major = average(stats.total_scanning_work_major, stats.major_collections);
  long long total_scanning_work = stats.total_scanning_work_minor + stats.total_scanning_work_major;
  int ring_operations_per_pool = average(stats.ring_operations, stats.total_alloced_pools);

  if (!boxroot_used() && total_scanning_work == 0) return;

  int64_t time_per_minor =
      stats.minor_collections ? stats.total_minor_time / stats.minor_collections : 0;
  int64_t time_per_major =
      stats.major_collections ? stats.total_major_time / stats.major_collections : 0;

  printf("POOL_LOG_SIZE: %d (%'d KiB, %'d roots/pool)\n"
         "POOL_ALIGNMENT: %'d kiB\n"
         "DEBUG: %d\n"
         "WITH_EXPECT: 1\n",
         (int)POOL_LOG_SIZE, kib_of_pools((int)1, 1), (int)POOL_ROOTS_CAPACITY,
         kib_of_pools(POOL_ALIGNMENT / POOL_SIZE,1),
         (int)DEBUG);

  printf("total allocated pool: %'d (%'d MiB)\n"
         "peak allocated pools: %'d (%'d MiB)\n"
         "total freed pool: %'d (%'d MiB)\n",
         stats.total_alloced_pools,
         kib_of_pools(stats.total_alloced_pools, 2),
         stats.peak_pools,
         kib_of_pools(stats.peak_pools, 2),
         stats.total_freed_pools,
         kib_of_pools(stats.total_freed_pools, 2));

  printf("work per minor: %'d\n"
         "work per major: %'d\n"
         "total scanning work: %'lld (%'lld minor, %'lld major)\n",
         scanning_work_minor,
         scanning_work_major,
         total_scanning_work, stats.total_scanning_work_minor, stats.total_scanning_work_major);

#if defined(POSIX_CLOCK)
  printf("average time per minor: %'lldns\n"
         "average time per major: %'lldns\n"
         "peak time per minor: %'lldns\n"
         "peak time per major: %'lldns\n",
         (long long)time_per_minor,
         (long long)time_per_major,
         (long long)stats.peak_minor_time,
         (long long)stats.peak_major_time);
#endif

  printf("total ring operations: %'d\n"
         "ring operations per pool: %'d\n",
         stats.ring_operations,
         ring_operations_per_pool);

#if DEBUG != 0
  printf("total created: %'d\n"
         "total deleted: %'d\n"
         "total modified: %'d\n",
         stats.total_create,
         stats.total_delete,
         stats.total_modify);

  printf("is_young_block: %'lld\n"
         "young hits: %d%%\n"
         "get_pool_header: %'lld\n"
         "is_pool_member: %'lld\n"
         "is_empty_free_list: %'lld\n",
         stats.is_young,
         (int)((stats.young_hit * 100) / stats.total_scanning_work_minor),
         stats.get_pool_header,
         stats.is_pool_member,
         stats.is_empty_free_list);
#endif
}

/* }}} */

/* {{{ Hook setup */

static void (*prev_scan_roots_hook)(scanning_action);

static void scanning_callback(scanning_action action)
{
  if (prev_scan_roots_hook != NULL) {
    (*prev_scan_roots_hook)(action);
  }
  if (in_minor_collection) ++stats.minor_collections;
  else ++stats.major_collections;
  // If no boxroot has been allocated, then scan_roots should not have
  // any noticeable cost. For experimental purposes, since this hook
  // is also used for other the statistics of other implementations,
  // we further make sure of this with an extra test, by avoiding
  // calling scan_roots if it has only just been initialised.
  CRITICAL_SECTION_BEGIN();
  if (boxroot_used()) {
    int64_t start = time_counter();
    scan_roots(action);
    int64_t duration = time_counter() - start;
    int64_t *total = in_minor_collection ? &stats.total_minor_time : &stats.total_major_time;
    int64_t *peak = in_minor_collection ? &stats.peak_minor_time : &stats.peak_major_time;
    *total += duration;
    if (duration > *peak) *peak = duration;
  }
  CRITICAL_SECTION_END();
}

static caml_timing_hook prev_minor_begin_hook = NULL;
static caml_timing_hook prev_minor_end_hook = NULL;

static void record_minor_begin()
{
  in_minor_collection = 1;
  if (prev_minor_begin_hook != NULL) prev_minor_begin_hook();
}

static void record_minor_end()
{
  in_minor_collection = 0;
  if (prev_minor_end_hook != NULL) prev_minor_end_hook();
}

static int setup = 0;

// Must be called to set the hook
int boxroot_setup()
{
  CRITICAL_SECTION_BEGIN();
  if (setup) {
    CRITICAL_SECTION_END();
    return 0;
  }
  // initialise globals
  in_minor_collection = 0;
  struct stats empty_stats = {0};
  stats = empty_stats;
  FOREACH_GLOBAL_RING(global, cl, { *global = NULL; });
  // save previous callbacks
  prev_scan_roots_hook = caml_scan_roots_hook;
  prev_minor_begin_hook = caml_minor_gc_begin_hook;
  prev_minor_end_hook = caml_minor_gc_end_hook;
  // install our callbacks
  caml_scan_roots_hook = scanning_callback;
  caml_minor_gc_begin_hook = record_minor_begin;
  caml_minor_gc_end_hook = record_minor_end;
  // we are done
  setup = 1;
  CRITICAL_SECTION_END();
  return 1;
}

void boxroot_teardown()
{
  CRITICAL_SECTION_BEGIN();
  if (!setup) {
    CRITICAL_SECTION_END();
    return;
  }
  // restore callbacks
  caml_scan_roots_hook = prev_scan_roots_hook;
  caml_minor_gc_begin_hook = prev_minor_begin_hook;
  caml_minor_gc_end_hook = prev_minor_end_hook;
  free_all_pools();
  setup = 0;
  CRITICAL_SECTION_END();
}

/* }}} */

/* {{{ */
/* }}} */
