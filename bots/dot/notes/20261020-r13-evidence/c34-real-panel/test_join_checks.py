"""Synthetic adversarial fixtures test parser rejection; never research observations."""
import hashlib,io,tempfile,unittest,zipfile
from pathlib import Path
import join_checks as j
class ParserChecks(unittest.TestCase):
 def test_original_real_archives(self):
  self.assertEqual(len(j.load('APEUSDT')),744);self.assertEqual(len(j.load('BTCUSDT')),744)
 def bad(self,kind):
  with zipfile.ZipFile(j.P/'raw/APEUSDT-1h-2023-05.zip') as z:lines=z.read(z.namelist()[0]).decode().splitlines()
  if kind=='missing':lines.pop()
  elif kind=='duplicate':lines[1]=lines[0]
  elif kind=='negative_volume':
   r=lines[0].split(',');r[5]='-1';lines[0]=','.join(r)
  elif kind=='bad_ohlc':
   r=lines[0].split(',');r[2]='0';lines[0]=','.join(r)
  elif kind=='bad_close_time':
   r=lines[0].split(',');r[6]=r[0];lines[0]=','.join(r)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'raw').mkdir();f=p/'raw/APEUSDT-1h-2023-05.zip'
   with zipfile.ZipFile(f,'w') as z:z.writestr('fixture.csv','\n'.join(lines))
   f.with_suffix('.zip.CHECKSUM').write_text(('0'*64 if kind=='checksum' else hashlib.sha256(f.read_bytes()).hexdigest())+' fixture')
   old=j.P;j.P=p
   try:
    with self.assertRaises(AssertionError):j.load('APEUSDT')
   finally:j.P=old
 def test_reject_missing(self):self.bad('missing')
 def test_reject_duplicate(self):self.bad('duplicate')
 def test_reject_negative_volume(self):self.bad('negative_volume')
 def test_reject_bad_ohlc(self):self.bad('bad_ohlc')
 def test_reject_close_time(self):self.bad('bad_close_time')
 def test_reject_checksum(self):self.bad('checksum')
if __name__=='__main__':unittest.main()
