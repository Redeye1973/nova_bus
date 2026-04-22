"""Decode WAV PCM from raw bytes — 8 / 16 / 32-bit PCM, mono or stereo."""
from __future__ import annotations

import io
import wave
from typing import Tuple

import numpy as np


def load_wav_pcm(data: bytes) -> Tuple[np.ndarray, int]:
    """Return samples float32 shape (n_frames, n_channels) in ~[-1,1], sample_rate."""
    bio = io.BytesIO(data)
    with wave.open(bio, "rb") as wf:
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if sw == 1:
        x = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        x = (x - 128.0) / 128.0
        x = x.reshape(nframes, nch) if nch > 1 else x
    elif sw == 2:
        flat = np.frombuffer(raw, dtype=np.int16)
        if nch > 1:
            if flat.size != nframes * nch:
                raise ValueError("wav_frame_count_mismatch")
            x = flat.reshape(nframes, nch).astype(np.float32) / 32768.0
        else:
            x = flat.astype(np.float32) / 32768.0
    elif sw == 4:
        flat = np.frombuffer(raw, dtype=np.int32)
        if nch > 1:
            if flat.size != nframes * nch:
                raise ValueError("wav_frame_count_mismatch")
            x = flat.reshape(nframes, nch).astype(np.float32) / 2147483648.0
        else:
            x = flat.astype(np.float32) / 2147483648.0
    elif sw == 3:
        nb = nframes * nch * 3
        if len(raw) < nb:
            raise ValueError("wav_24bit_truncated")
        b = np.frombuffer(raw[:nb], dtype=np.uint8).reshape(-1, 3)
        x24 = b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16)
        x24 = np.where(x24 >= 0x800000, x24 - 0x1000000, x24).astype(np.float32) / 8388608.0
        if nch > 1:
            if x24.size != nframes * nch:
                raise ValueError("wav_24bit_shape")
            x = x24.reshape(nframes, nch)
        else:
            x = x24
    else:
        raise ValueError(f"unsupported_sample_width:{sw}")
    return x, int(sr)
