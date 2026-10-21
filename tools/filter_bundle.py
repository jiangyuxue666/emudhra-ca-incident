import re, subprocess, sys
src, out = sys.argv[1], sys.argv[2]
data = open(src, 'r', encoding='utf-8', errors='surrogateescape').read()
block_re = re.compile(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----\s*', re.S)
blocks = list(block_re.finditer(data))
removed, kept_certs = [], 0
pieces, last = [], 0
for m in blocks:
    pem = m.group(0)
    p = subprocess.run(['openssl','x509','-noout','-subject'], input=pem.encode(),
                       capture_output=True)
    subj = p.stdout.decode().strip()
    if 'emSign ECC Root CA - G3' in subj:
        removed.append(subj)
        pieces.append(data[last:m.start()])
    else:
        kept_certs += 1
        pieces.append(data[last:m.end()])
    last = m.end()
pieces.append(data[last:])
if len(removed) != 1:
    sys.exit(f"refusing: matched {len(removed)} emSign G3 blocks, expected exactly 1: {removed}")
open(out, 'w', encoding='utf-8', errors='surrogateescape').write(''.join(pieces))
print(f"removed {len(removed)}: {removed[0]}")
print(f"certs before={len(blocks)} after={kept_certs}")
