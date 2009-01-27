/* mhash_whirlpool.h
 * 
 * The Whirlpool hashing function. A new 512-bit hashing function
 * operating on messages less than 2 ** 256 bits in length. The
 * function structure is designed according to the Wide Trail strategy
 * and permits a wide variety of implementation trade-offs.
 *
 * The following code was written by B. Poettering for the mhash library.
 * The code is in the public domain. See whirlpool.c for more information.
 *
 * This code was modified by Mathew Ryden of ESP Metanational, LLP. This
 * code is in the public domain.
 * */

#if !defined(__MHASH_WHIRLPOOL_H_INCLUDED)
#define __MHASH_WHIRLPOOL_H_INCLUDED


#define WHIRLPOOL_DIGEST_SIZE 64
#define WHIRLPOOL_DATA_SIZE 64

typedef unsigned long long u64;
typedef unsigned long u32;
typedef unsigned char u8;

typedef struct whirlpool_ctx
{
  u8 buffer[WHIRLPOOL_DATA_SIZE];	   /* buffer of data to hash */
  u64 hashlen[4];                       /* number of hashed bits (256-bit) */
  u32 index;		                   /* index to buffer */
  u64 hash[WHIRLPOOL_DIGEST_SIZE/8];    /* the hashing state */
} hash_state;

void
whirlpool_init(struct whirlpool_ctx *ctx);

void
whirlpool_update(struct whirlpool_ctx *ctx, __const u8 *data, u32 length);

void
whirlpool_final(struct whirlpool_ctx *ctx);

void
whirlpool_digest(__const struct whirlpool_ctx *ctx, u8 *digest);


#endif   /* __MHASH_WHIRLPOOL_H_INCLUDED */

