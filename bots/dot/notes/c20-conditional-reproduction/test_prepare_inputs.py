import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

import prepare_inputs as p


class PreparationTests(unittest.TestCase):
    def fixture(self, root, member='sample.csv'):
        content = b'1704067200000,100,110,90,105,2,1704153599999,200,2,1,100,0\n'
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr(member, content)
        payload = buffer.getvalue()
        path = root / 'sample.zip'
        path.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        path.with_name(path.name + '.CHECKSUM').write_text(digest + '  sample.zip\n')
        return {'relative_archive': 'sample.zip', 'archive_sha256': digest, 'csv_member': 'sample.csv', 'csv_uncompressed_bytes': len(content)}

    def test_verified_archive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = self.fixture(root)
            self.assertEqual(p.archive_rows(root, item)[0][0], '1704067200000')

    def test_changed_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = self.fixture(root)
            (root / 'sample.zip.CHECKSUM').write_text('0' * 64 + '  sample.zip')
            with self.assertRaises(ValueError):
                p.archive_rows(root, item)

    def test_changed_archive_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = self.fixture(root)
            (root / 'sample.zip').write_bytes(b'not an archive')
            with self.assertRaises(ValueError):
                p.archive_rows(root, item)

    def test_unexpected_member_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = self.fixture(root, '../sample.csv')
            with self.assertRaises(ValueError):
                p.archive_rows(root, item)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item = self.fixture(root)
            item['relative_archive'] = '../sample.zip'
            with self.assertRaises(ValueError):
                p.archive_rows(root, item)

    def test_oversized_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'large'
            with path.open('wb') as out:
                out.truncate(p.LIMIT + 1)
            with self.assertRaises(ValueError):
                p.bounded_read(path)

    def test_ms_us_same_instant(self):
        self.assertEqual(p.to_us('1704067200000')[0], p.to_us('1704067200000000')[0])
        with self.assertRaises(ValueError):
            p.to_us('1704067200')

    def test_header_order(self):
        fields = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'count', 'taker_buy_volume', 'taker_buy_quote_volume', 'ignore']
        p.validate_header(fields, 'klines')
        fields[1], fields[2] = fields[2], fields[1]
        with self.assertRaises(ValueError):
            p.validate_header(fields, 'klines')

    def test_mark_ignore_is_not_traded_volume(self):
        raw = ['1704067200000', '100', '110', '90', '105', 'ignore', '1704153599999', 'ignore', 'ignore', 'ignore', 'ignore', 'ignore']
        item = {'symbol': 'BTCUSDT_241227', 'kind': 'markPriceKlines', 'archive_url': 'https://data.binance.vision/example.zip'}
        self.assertEqual(p.parse_row(raw, item, 2)['volume_semantics'], 'IGNORE (official mark documentation)')

    def test_bad_ohlc_rejected(self):
        raw = ['1704067200000', '100', '99', '90', '105', '2', '1704153599999', '200', '2', '1', '100', '0']
        item = {'symbol': 'BTCUSDT', 'archive_url': 'https://data.binance.vision/example.zip'}
        with self.assertRaises(ValueError):
            p.parse_row(raw, item, 1)


if __name__ == '__main__':
    unittest.main()
