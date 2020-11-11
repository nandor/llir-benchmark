#include <caml/mlvalues.h>
#include <sys/time.h>

CAMLprim value ocaml_read_time_stamp_counter()
{
#ifdef __x86_64__
  return Val_long( __rdtsc() );
#else
  struct timeval tv;
  gettimeofday(&tv, NULL);
  return (long long)(tv.tv_sec) * 1000000ll + tv.tv_usec;
#endif
}
