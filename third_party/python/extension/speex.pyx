#@+leo-ver=4
#@+node:@file speex.pyx
#@@language python
"""
speex.pyx

Python wrapper for Speex speech codec (www.speex.org)
Defines a 'speex' object through which encoding and
decoding of audio data can be performed.
"""

version = "0.2"

#@+others
#@+node:cdef externs
# basic system and python facilities

#@+others
#@+node:string.h
cdef extern from "string.h":

    cdef void *memset(void *s, int c, int n)
    cdef void *memcpy(void *dest, void *src, int n)
#@-node:string.h
#@+node:stdio.h
cdef extern from "stdio.h":
    int printf(char *format,...)

#@-node:stdio.h
#@+node:stdlib.h
cdef extern from "stdlib.h":
    void *malloc(int size)
    void *realloc(void *ptr, int size)
    void free(void *ptr)

#@-node:stdlib.h
#@+node:math.h
cdef extern from "math.h":
    double fabs(double x)

#@-node:math.h
#@+node:Python.h
# Python-specifics

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *, int)

#@-node:Python.h
#@+node:speex.h
# Speex-specifics

cdef extern from "speex.h":
    ctypedef struct SpeexBits:
        char *bytes   # "raw" data
        int  nbBits   # Total number of bits stored in the stream
        int  bytePtr  # Position of the byte "cursor"
        int  bitPtr   # Position of the bit "cursor" within the current byte
        int  owner    # Does the struct "own" the "raw" buffer (member "bytes")
        int  overflow # Set to one if we try to read past the valid data
        int  buf_size # Allocated size for buffer

    ctypedef struct SpeexMode:
        void *mode

    cdef enum SPEEX_SYMBOLS:
        SPEEX_SET_QUALITY
        SPEEX_GET_FRAME_SIZE
        SPEEX_SET_ENH
        SPEEX_GET_ENH

    cdef SpeexMode speex_nb_mode

    cdef void speex_bits_init(SpeexBits *bits)
    cdef void speex_bits_read_from(SpeexBits *bits, char *bytes, int len)
    cdef int speex_bits_write(SpeexBits *bits, char *bytes, int max_len)
    cdef void speex_bits_reset(SpeexBits *bits)
    cdef void speex_bits_destroy(SpeexBits *bits)

    cdef void *speex_encoder_init(SpeexMode *mode)
    cdef int speex_encoder_ctl(void *state,
                               int request,
                               void *ptr)

    cdef int speex_encode(void *state, float *inbuf, SpeexBits *bits)

    cdef void speex_encoder_destroy(void *state)

    cdef void *speex_decoder_init(SpeexMode *mode)
    int speex_decoder_ctl(void *state, int request, void *ptr)
    cdef int speex_decode(void *state,
                          SpeexBits *bits,
                          float *out)
    cdef void speex_decoder_destroy(void *state)
#@-node:speex.h
#@-others
#@-node:cdef externs
#@+node:cdef class new
cdef class new:

    #@    @+others
    #@+node:c attribs
    cdef void *encState
    cdef int encQuality
    cdef int encFramesPerBlock
    cdef float *encBuf
    cdef float *encPtr
    cdef int encNumFrames
    cdef SpeexBits encBits
    cdef int raw
    
    # Data for decoding
    cdef void *decState
    cdef int decQuality
    cdef unsigned char *decBuf
    cdef unsigned char *decPtr
    cdef unsigned short decBlkSize
    cdef int decNumBytes
    cdef int decPhase
    cdef int decEnhanceOn
    cdef SpeexBits decBits
    cdef public object debug
    
    cdef public object endianness
    #@-node:c attribs
    #@+node:__init__
    def __init__(self, quality=8, raw=0, **kw):
        """
        Create a new speex speech stream object
    
        Arguments:
         - quality - 0 (lowest) to 10 (highest), default 8
    
         - raw - set to 1 for encoding from and decoding to string, default 0
    
        Keywords:
         - debug - set to 1 to issue debug messages, default 0
    
        The created speex stream object has two methods:
         - encode - encode a block of speech audio data
    
           Arguments:
            - block of audio data, as sequence of frames, where
              each frame is an int
    
           Returns:
            - raw string containing encoded data, or
              empty string if there is not yet any encoded
              data available
    
         - decode - decodes a block of speech audio data
    
           Arguments:
            - block of encoded data, as raw string,
    
           Returns:
            - block of audio data, as sequence of ints, or
              an empty sequence if there is no decoded data
              available yet
    
        Notes:
         - Both of these methods use internal buffering, which means that
           you can feed in data piecemeal. This helps a lot when sending and
           receiving data over the net.
        """
    
        cdef int is_raw
        #cdef SpeexMode speex_nb_mode
    
        # Set up encoder
        self.encState = speex_encoder_init(&speex_nb_mode)
    
        self.encQuality = quality
        is_raw = raw
        self.raw = is_raw
        self.debug = int(kw.get('debug', 0))
    
        speex_encoder_ctl(self.encState, SPEEX_SET_QUALITY, &self.encQuality)
    
        #printf("speex1: using new pyrex wrapper, quality=%d\n", self.encQuality)
    
        speex_encoder_ctl(self.encState, SPEEX_GET_FRAME_SIZE, &self.encFramesPerBlock)
        #printf("encoder frame size=%d\n", self.encFramesPerBlock)
        self.encBuf = <float *>malloc(self.encFramesPerBlock * sizeof(float))
        if not self.encBuf:
            raise Exception("Out of memory")
        memset(self.encBuf, 0, self.encFramesPerBlock * sizeof(float))
        self.encNumFrames = 0
        self.encPtr = self.encBuf
        speex_bits_init(&self.encBits)
    
        #  Set up decoder
        self.decState = speex_decoder_init(&speex_nb_mode)
        self.decEnhanceOn = 1
        speex_decoder_ctl(self.decState, SPEEX_SET_ENH, &self.decEnhanceOn)
        self.decBuf = <unsigned char *>malloc(2) # just big enough for leading length field
        self.decPhase = 0
        if not self.decBuf:
            raise Exception("Out of memory")
        self.decPtr = self.decBuf
        self.decNumBytes = 0
        speex_bits_init(&self.decBits)
    #@-node:__init__
    #@+node:__dealloc__
    def __dealloc__(self):
        # Destroy the encoder state and data
        speex_encoder_destroy(self.encState)
        if self.encBuf:
            free(self.encBuf)
    
        # Destroy the decoder state
        speex_decoder_destroy(self.decState)
        if self.decBuf:
            free(self.decBuf)
    
        # Destroy the bit-packing structs
        speex_bits_destroy(&self.encBits)
        speex_bits_destroy(&self.decBits)
    
    #@-node:__dealloc__
    #@+node:encode
    def encode(self, input, raw=None):
        """
        Encode some audio data
    
        Arguments:
         - data - sequence of audio frames to encode, OR string of 16-bit frames
    
         - raw  - true if data being passed in is a string of 16-bit frames
           defaults to whatever raw arg was passed to constructor
    
        Returns:
         - raw string with encoded data
        """
    
        cdef int numInputFrames
        cdef float *framesBuf, *framesPtr
        # cdef float thisframe
        cdef int i
        cdef int totFrames
        # cdef SpeexBits bits;
        cdef int cbitsSiz
        # cdef int cbitsSiz = 2048
        # cdef char cbits[cbitsSiz]
        cdef char cbits[2048]
        cdef int nBlocks
        cdef int nBytes
        cdef char *bufOut
        cdef int bufOutSiz
        cdef int remainder
    
        cdef char *rawbuf
        cdef short *frameptr
    
        cbitsSiz = self.encFramesPerBlock * 5 / 4
        bufOut = <char *>malloc(0)
        bufOutSiz = 0
    
        inputFramesList = []
    
        #printf("encode: ok1\n")
    
        # override raw flag if user has passed in a string
        if raw is None:
            raw = self.raw
        if type(input) is type(""):
            raw = 1
     
        # Determine number of frames
        if raw:
            numInputFrames = len(input) / 2 #  hardwired 16-bit frames
        else:
            numInputFrames = len(input)
    
        #printf("encode: ok2\n")
    
        # printf("enc - numInputFrames = %d\n", numInputFrames)
    
        if numInputFrames == 0:
            return ''
    
        #printf("encode: ok3\n")
    
        # Encode what we have, block by block
        totFrames = numInputFrames + self.encNumFrames
    
        #printf("totFrames=%d, input data size=%d\n",
        #       totFrames, totFrames * sizeof(short))
    
        framesBuf = <float *>malloc(totFrames * sizeof(float))
        framesPtr = framesBuf
        if not framesBuf:
            raise Exception("Out of memory")
    
        #printf("encode: ok4\n")
    
        #  Copy in the fragments we have in buffer
        # printf("copying in buf of %d frames\n", self.encNumFrames)
        for i from 0 <= i < self.encNumFrames:
            framesPtr[i] = self.encBuf[i]
    
        #printf("encode: ok4a = i=%d, self.encNumFrames=%d\n",
        #       i, self.encNumFrames)
    
        framesPtr = framesPtr + i
    
        #printf("encode: ok5\n")
    
        # Extract the rest from input sequence, depending on whether input is str or list
        # printf("copying extra %d frames from input\n", numInputFrames);
        if raw:
            rawbuf = input
            frameptr = <short *>rawbuf
            for i from 0 <= i < numInputFrames:
                #  assume little-endian - sorry, mac hackers
                # frame = rawptr[0] + 256 * rawptr[1]
                # rawptr += 2
                # *framesPtr++ = (float)frame
    
                framesPtr[i] = frameptr[i]
            framesPtr = framesPtr + i
            frameptr = frameptr + i
            # thisframe = *frameptr++
            # if (i < 10)
            # {
            #   printf("encode: thisframe=%f\n", thisframe)
            # }
            # *framesPtr++ = thisframe
    
        else:
            for i from 0 <= i < numInputFrames:
                framesPtr[i] = input[i]
            framesPtr = framesPtr + i
            # thisframe = PyInt_AsLong(PyList_GetItem(input, i))
            # if (i < 10)
            # {
            #   printf("encode: thisframe=%f\n", thisframe)
            # }
            # *framesPtr++ = thisframe
    
        #printf("written %d frames to buf\n", framesPtr - framesBuf)
    
        #printf("encode: ok6\n")
    
        #  Encode these frames
        nBlocks = totFrames / self.encFramesPerBlock
        framesPtr = framesBuf
        for i from 0 <= i < nBlocks:
            # printf("seeking to encode a block, nBlocks=%d\n", nBlocks)
            speex_bits_reset(&self.encBits)
            # printf("ok1 - state=0x%lx, buf=0x%lx, bits=0x%lx\n",
            # self.encState, framesBuf, &self.encBits)
            speex_encode(self.encState, framesPtr, &self.encBits)
            # printf("ok2\n")
            nBytes = speex_bits_write(&self.encBits, cbits, cbitsSiz)
            #printf("nBytes=%d\n", nBytes)
            bufOut = <char *>realloc(bufOut, bufOutSiz+nBytes+2)
            # printf("ok4\n")
            #  write out 2 length bytes
            bufOut[bufOutSiz] = nBytes % 256
            bufOut[bufOutSiz+1] = nBytes / 256
            bufOutSiz = bufOutSiz + 2
            memcpy(bufOut+bufOutSiz, cbits, nBytes)
            # printf("ok5\n")
            bufOutSiz = bufOutSiz + nBytes
            # printf("ok6\n")
    
            framesPtr = framesPtr + self.encFramesPerBlock
    
        #printf("encode: ok7\n")
    
        #  stick remainder, if any, into buffer
        self.encNumFrames = totFrames - (nBlocks * self.encFramesPerBlock)
        remainder = self.encNumFrames * sizeof(float)
        memcpy(self.encBuf, framesPtr, remainder)
        # memset(self.encBuf, 0, self.encFramesPerBlock * sizeof(float))
        # printf("encNumFrames=%d\n", self.encNumFrames)
        # printf("remainder=%d\n", remainder)
    
        #printf("encode: ok8\n")
    
        #  ditch temp buffer
        free(framesBuf)
    
        #printf("encode: ok9\n")
    
        #  pass back encoded buffer as raw string
        #printf("bufOutSize=%d\n", bufOutSiz)
        return PyString_FromStringAndSize(bufOut, bufOutSiz)
    
    
    #@-node:encode
    #@+node:decode
    def decode(self, input, raw=None):
        """
        Decode an encoded block, return as sequence of frame tuples
    
        Arguments:
          - encoded - raw string, containing encoded data
          - raw - True if data is to be returned as string of 16-bit frames, defaults to
            whatever raw value was passed to constructor
    
        Returns:
          - decoded blocks, as sequence of frames, where each frame
            or a string of these 16-bit frames if raw is True
            is an int
        """
    
        cdef unsigned char *encBuf
        cdef unsigned char *encBufEnd
        cdef unsigned char *encPtr
        cdef int encBufLen
        cdef int numDecFrames #  number of decoded frames
        # cdef int cbitsSiz
        # cdef char cbits[cbitsSiz]
        cdef float *decFloats
        cdef float *decFloats1
        cdef short *decShorts
        cdef short *decShorts1
        cdef int decBlocks
        cdef int i
        cdef int is_raw
        cdef int needed
        cdef int newNumFrames
        cdef char *tmp
    
        #printf("decode: ok1\n")
    
        tmp = input
        encBuf = <unsigned char *>tmp
        encBufEnd = NULL
        encPtr = NULL
        encBufLen = 0
        decFloats = <float *>malloc(0)
        decShorts = <short *>malloc(0)
        decBlocks = 0
    
        if raw is None:
            raw = self.raw
        is_raw = raw
    
        #printf("decode: ok2, raw=%d\n", is_raw)
    
        #  We get an earlymark if caller provided no data
        encBufLen = len(input)
        if encBufLen == 0:
            if is_raw:
                return ''
            else:
                return []
    
        #printf("decode: ok3\n")
    
        #  decode the sucker
        encPtr = encBuf
        encBufEnd = encBuf + encBufLen
    
        #printf("decode: ok4, len=%d\n", encBufLen)
    
        while encPtr < encBufEnd:
            #  state depends on whether we've received the block header count bytes
            if self.decPhase == 0:
                #  Grab LSB of block size
                self.decBuf[0] = encPtr[0]
                #printf("decode: ok4a - LSB=%02x\n", encPtr[0])
                self.decPhase = 1
                encPtr = encPtr + 1
                encBufLen = encBufLen - 1
                continue
            elif self.decPhase == 1:
                #  Grab MSB of block size and determine total block size
                self.decBuf[1] = encPtr[0]
                #printf("decode: ok4b - LSB=%02x\n", encPtr[0])
                self.decBlkSize = self.decBuf[0] + 256 * self.decBuf[1]
      
                #  resize dec buffer to suit
                #  todo - find better way to sanity check the size
                self.decBuf = <unsigned char *>realloc(
                    <void *>self.decBuf,
                    self.decBlkSize)
                self.decPtr = self.decBuf
                self.decNumBytes = 0
                self.decPhase = 2
                encPtr = encPtr + 1
                encBufLen = encBufLen - 1
                continue
            else:
                #printf("decode: ok4c siz=%d decnumbytes=%d\n",
                #       self.decBlkSize, self.decNumBytes)
                needed = self.decBlkSize - self.decNumBytes
      
                #printf("decode: ok4d encBufLen=%d needed=%d\n",
                #       encBufLen, needed)
                #  do we have enough input data to complete a frame?
                if encBufLen >= needed:
                    newNumFrames = (decBlocks + 1) * self.encFramesPerBlock
      
                    #  great - decode frame and add to our array of shorts
                    memcpy(self.decPtr,
                           encPtr,
                           self.decBlkSize - self.decNumBytes)
                    encPtr = encPtr + needed
                    encBufLen = encBufLen - needed
      
                    #  do the decoding
                    #  expand shorts and floats buffers
                    decShorts = <short *>realloc(decShorts, newNumFrames * sizeof(short))
                    decShorts1 = decShorts + decBlocks * self.encFramesPerBlock
                    decFloats = <float *>realloc(decFloats, newNumFrames * sizeof(float))
                    decFloats1 = decFloats + decBlocks * self.encFramesPerBlock
      
                    # Copy the data into the bit-stream struct
                    speex_bits_read_from(&self.decBits, <char *>self.decPtr, self.decBlkSize)
      
                    # Decode the data
                    speex_decode(self.decState, &self.decBits, decFloats1)
      
                    # Copy from float to short (16 bits) for output
                    for i from 0 <= i < self.encFramesPerBlock:
                      # decShorts1[i] = decFloats1[i]
                      decShorts1[i] = <short>decFloats1[i]
      
                    self.decPhase = 0 #  back to awaiting LSB of count header
                    self.decNumBytes = 0
                    if self.debug:
                        printf("self.decBuf=%lx\n", self.decBuf)
                    self.decBuf = <unsigned char *>realloc(self.decBuf, 2)
                    decBlocks = decBlocks + 1
                    continue
                else:
                    #printf("decode: ok4e\n")
    
                    #  not enough to decode another speex frame - just stick into buffer
                    if self.debug:
                        printf("decPtr=%lx, encPtr=%lx, encBufLen=%d\n",
                                self.decPtr, encPtr, encBufLen)
                    memcpy(self.decPtr, encPtr, encBufLen)
                    self.decPtr = self.decPtr + encBufLen
                    encBufLen = 0
                    break
    
        #printf("decode: ok5\n")
    
        #  did we get anything?
        if decBlocks > 0:
            numDecFrames = decBlocks * self.encFramesPerBlock
           
            if is_raw:
                ret = PyString_FromStringAndSize(<char *>decShorts, numDecFrames * 2)
            else:
                #  build up a sequence of tuples
                ret = []
                for i in range(numDecFrames):
                    ret.append(decShorts[i])
        else:
            if is_raw:
                ret = ""
            else:
                ret = []
    
        #printf("decode: ok6\n")
    
        free(decShorts)
        free(decFloats)
        return ret
    
        # return Py_BuildValue("s#", decBuf, decBufLen)
    
    
    #@-node:decode
    #@-others
#@-node:cdef class new
#@-others
#@-node:@file speex.pyx
#@-leo
