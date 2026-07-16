import os
import shutil

src_dir = None
for d in os.listdir('.'):
    if '進階' in d:
        src_dir = d
        break

if not src_dir:
    # try looking for any folder containing '3443' and 'V38' file
    for d in os.listdir('.'):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if '3443' in f and 'V38' in f and f.endswith('.xlsx'):
                    src_dir = d
                    break

if src_dir:
    for f in os.listdir(src_dir):
        if '3443' in f and 'V38' in f and f.endswith('.xlsx'):
            src_file = os.path.join(src_dir, f)
            print("Found source:", src_file)
            
            # Find destination
            for d2 in os.listdir('.'):
                if 'V6_Server' in d2:
                    dst_dir = os.path.join(d2, 'data')
                    dst_file = os.path.join(dst_dir, '3443_創意_V_Rebound_高勝率回測.xlsx')
                    print("Copying to:", dst_file)
                    shutil.copy(src_file, dst_file)
                    break
