"""Put the Korean karaoke movie (made in the GC project, same source file) into work/patched.

GC and Wii ship the identical movie/karaoke_teriyaki.thp, so the GC-made Korean THP is used as is.
Keep a copy at work/movie/karaoke_teriyaki_ko.thp (not committed: it holds game video).
"""
import hashlib
from port_common import ROOT, ORIGINAL

NAME = 'movie/karaoke_teriyaki.thp'
ORIGINAL_MD5 = '8d84b1348aae4f2b23c549b80c0c5e1c'
KOREAN_MD5 = '3ca37955976f8c5917b064a8bd2fdbbc'


def main():
    md5 = lambda b: hashlib.md5(b).hexdigest()
    orig = (ORIGINAL / 'files' / NAME).read_bytes()
    assert md5(orig) == ORIGINAL_MD5, 'original movie differs'
    ko = (ROOT / 'work/movie/karaoke_teriyaki_ko.thp').read_bytes()
    assert md5(ko) == KOREAN_MD5 and ko[:4] == b'THP\x00', 'Korean movie differs'
    dst = ROOT / 'work/patched/files' / NAME
    dst.write_bytes(ko)
    assert md5(dst.read_bytes()) == KOREAN_MD5
    print('PASS karaoke movie', len(orig), '->', len(ko), KOREAN_MD5)


if __name__ == '__main__':
    main()
