import unittest
import sessionization as sessionize
from datetime import datetime
from datetime import timedelta
from io import StringIO


class TestSerialization(unittest.TestCase):

    def setUp(self):
        self.time0 = datetime.strptime('2017-06-30 00:00:00', '%Y-%m-%d %H:%M:%S')
        self.time1 = datetime.strptime('2017-06-30 00:00:01', '%Y-%m-%d %H:%M:%S')
        self.time2 = datetime.strptime('2017-06-30 00:00:02', '%Y-%m-%d %H:%M:%S')
        self.time3 = datetime.strptime('2017-06-30 00:00:03', '%Y-%m-%d %H:%M:%S')
        self.time4 = datetime.strptime('2017-06-30 00:00:04', '%Y-%m-%d %H:%M:%S')
        self.time5 = datetime.strptime('2017-06-30 00:00:05', '%Y-%m-%d %H:%M:%S')
        self.time6 = datetime.strptime('2017-06-30 00:00:06', '%Y-%m-%d %H:%M:%S')

    def test_extract_required_fields_order(self):
        self.assertEqual(sessionize.extract_required_fields_order(
                'ip,date,time,zone,cik,accession,extention,code,size,idx,norefer,noagent,find,crawler,browser',
                ['ip', 'date', 'time', 'cik', 'accession', 'extention']),
                (0, 1, 2, 4, 5, 6))
        with self.assertRaises(Exception):
            sessionize.extract_required_fields_order(
                'ip,date,time,zone,cik,accession,extention,code,size,idx,norefer,noagent,find,crawler,browser',
                ['ip', 'date', 'time', 'cik', 'accession', 'extention1'])
            sessionize.extract_required_fields_order(
                'ip,date,time,zone,cik,accession,extention,code,size,idx,norefer,noagent,find,crawler,browser',
                ['ip', 'date', 't', 'cik', 'accession'])

    def test_check_field_validity_and_cleanup(self):
        ip, d, t, cik, accession, extention, last_date_time = (
            '121.40.65.ebc', '2017-06--28', '00:00:00', '1592016.0', '0000899243-17-017281', '-index.htm', None)
        chk = sessionize.check_field_validity_and_cleanup(ip, d, t, cik, accession, extention, last_date_time)
        self.assertFalse(chk[0])

        ip, d, t, cik, accession, extention, last_date_time = (
            '121.40.65.ebc', '2017-06--28', '1:05:12', '1592016.0', '0000899243-17-017281', '-index.htm', None)
        chk = sessionize.check_field_validity_and_cleanup(ip, d, t, cik, accession, extention, last_date_time)
        self.assertFalse(chk[0])

        ip, d, t, cik, accession, extention, last_date_time = (
            '  ', '2017-06-28', '00:00:00', '1592016.0', '0000899243-17-017281', '-index.htm', None)
        chk = sessionize.check_field_validity_and_cleanup(ip, d, t, cik, accession, extention, last_date_time)
        self.assertFalse(chk[0])

        tmp_datetime = datetime(2017, 6, 28)
        ip, d, t, cik, accession, extention, last_date_time = (
            '121.40.65.ebc', '2017-06-28', '00:00:00', '1592016.0', '0000899243-17-017281', '-index.htm', None)
        chk = sessionize.check_field_validity_and_cleanup(ip, d, t, cik, accession, extention, last_date_time)
        self.assertTrue(chk[0])
        self.assertTupleEqual(chk[1],
                              ('121.40.65.ebc', tmp_datetime, '1592016.0', '0000899243-17-017281', '-index.htm'))

        tmp_datetime = datetime(2017, 6, 28)
        ip, d, t, cik, accession, extention, last_date_time = (
            ' 121.40.65.ebc ', ' 2017-06-28 ', '2:00:00 ', '   1592016.0', '0000899243-17-017281  ', ' -index.htm',
            tmp_datetime)
        chk = sessionize.check_field_validity_and_cleanup(ip, d, t, cik, accession, extention, last_date_time)
        self.assertTrue(chk[0])
        self.assertTupleEqual(chk[1],
                              ('121.40.65.ebc', tmp_datetime, '1592016.0', '0000899243-17-017281', '-index.htm'))

    def test_extract_required_fields(self):
        req_fields = {'ip': 0, 'date': 1, 'time': 2, 'cik': 4, 'accession': 5, 'extention': 6}
        record_string = '121.40.65.ebc,2017-06-28,00:00:00,0.0,1592016.0,0000899243-17-017281,-index.htm,301.0,' \
                        '684.0,1.0,0.0,0.0,10.0,0.0,'
        (ip, date, time, cik, accession, extention) = sessionize.extract_required_fields(record_string, req_fields)
        self.assertTupleEqual((ip, date, time, cik, accession, extention),
                              ('121.40.65.ebc', '2017-06-28', '00:00:00', '1592016.0', '0000899243-17-017281',
                               '-index.htm'))

        req_fields = {'ip': 12, 'date': 1, 'time': 0, 'cik': 3, 'accession': 4, 'extention': 6}
        record_string = '00:00:00,2017-06-28,0.0,1592016.0,0000899243-17-017281,301.0,-index.htm,' \
                        '684.0,1.0,0.0,0.0,10.0,121.40.65.ebc,0.0,'
        (ip, date, time, cik, accession, extention) = sessionize.extract_required_fields(record_string, req_fields)
        self.assertTupleEqual((ip, date, time, cik, accession, extention),
                              ('121.40.65.ebc', '2017-06-28', '00:00:00', '1592016.0', '0000899243-17-017281',
                               '-index.htm'))

    def test_get_order_of_required_fields(self):
        input_handle = StringIO(
            'ip,date,time,zone,cik,accession,extention,code,size,idx,norefer,noagent,find,crawler,browser\n' +
            '101.81.133.jja,2017-06-30,00:00:00,0.0,1608552.0,0001047469-17-004337,-index.htm,200.0,80251.0,1.0,0.0,'
            '0.0,9.0,0.0,\n')
        self.assertDictEqual(sessionize.get_order_of_required_fields(input_handle),
                             dict(zip(['ip', 'date', 'time', 'cik', 'accession', 'extention'], [0, 1, 2, 4, 5, 6])))

        input_handle = StringIO(
            'ip,zone,cik,accession,extention,time,code,size,idx,date,norefer,noagent,find,crawler,browser\n' +
            '101.81.133.jja,2017-06-30,00:00:00,0.0,1608552.0,0001047469-17-004337,-index.htm,200.0,80251.0,1.0,0.0,'
            '0.0,9.0,0.0,\n')
        self.assertDictEqual(sessionize.get_order_of_required_fields(input_handle),
                             dict(zip(['ip', 'date', 'time', 'cik', 'accession', 'extention'],
                                      [0, 9, 5, 2, 3, 4])))

    def test_write_closed_sessions(self):
        inactivity_interval = 2

        request_dict = {'101.81.133.jja': [self.time0, self.time0, 1, 1],
                        '107.23.85.jfd': [self.time0, self.time0, 2, 2]}
        expiration_dict = {self.time2: ['101.81.133.jja', '107.23.85.jfd']}
        output_handle = StringIO()
        sessionize.write_closed_sessions(output_handle, self.time0, self.time0 - timedelta(seconds=1),
                                         inactivity_interval, request_dict, expiration_dict)
        self.assertEqual(output_handle.getvalue(), '')

        request_dict = {'101.81.133.jja': [self.time0, self.time0, 1, 1],
                        '107.23.85.jfd': [self.time0, self.time1, 3, 2],
                        '108.91.91.hbc': [self.time1, self.time1, 1, 1]}
        expiration_dict = {self.time2: ['101.81.133.jja', '107.23.85.jfd'],
                           self.time3: ['107.23.85.jfd', '108.91.91.hbc']}
        output_handle = StringIO()
        sessionize.write_closed_sessions(output_handle, self.time1, self.time1 - timedelta(seconds=1),
                                         inactivity_interval, request_dict, expiration_dict)
        self.assertEqual(output_handle.getvalue(), '')

        request_dict = {'101.81.133.jja': [self.time0, self.time0, 1, 1],
                        '107.23.85.jfd': [self.time0, self.time1, 3, 2],
                        '108.91.91.hbc': [self.time1, self.time1, 1, 1],
                        '106.120.173.jie': [self.time2, self.time2, 1, 1],
                        '107.178.195.aag': [self.time2, self.time2, 1, 2]}
        expiration_dict = {self.time2: ['101.81.133.jja', '107.23.85.jfd'],
                           self.time3: ['107.23.85.jfd', '108.91.91.hbc'],
                           self.time4: ['106.120.173.jie', '107.178.195.aag']}
        output_handle = StringIO()
        sessionize.write_closed_sessions(output_handle, self.time2, self.time2 - timedelta(seconds=1),
                                         inactivity_interval, request_dict, expiration_dict)
        self.assertEqual(output_handle.getvalue(), '101.81.133.jja,2017-06-30 00:00:00,2017-06-30 00:00:00,1,1\n')
        self.assertDictEqual(request_dict, {'107.23.85.jfd': [self.time0, self.time1, 3, 2],
                                            '108.91.91.hbc': [self.time1, self.time1, 1, 1],
                                            '106.120.173.jie': [self.time2, self.time2, 1, 1],
                                            '107.178.195.aag': [self.time2, self.time2, 1, 2]})
        self.assertDictEqual(expiration_dict, {self.time3: ['107.23.85.jfd', '108.91.91.hbc'],
                                               self.time4: ['106.120.173.jie', '107.178.195.aag']})

        request_dict = {'107.23.85.jfd': [self.time0, self.time3, 4, 2],
                        '108.91.91.hbc': [self.time1, self.time1, 1, 1],
                        '106.120.173.jie': [self.time2, self.time2, 1, 1],
                        '107.178.195.aag': [self.time2, self.time2, 1, 2]}
        expiration_dict = {self.time3: ['107.23.85.jfd', '108.91.91.hbc'],
                           self.time4: ['106.120.173.jie', '107.178.195.aag'],
                           self.time5: ['107.23.85.jfd']}
        output_handle = StringIO()
        sessionize.write_closed_sessions(output_handle, self.time3, self.time3 - timedelta(seconds=1),
                                         inactivity_interval, request_dict, expiration_dict)
        self.assertEqual(output_handle.getvalue(), '108.91.91.hbc,2017-06-30 00:00:01,2017-06-30 00:00:01,1,1\n')
        self.assertDictEqual(request_dict, {'107.23.85.jfd': [self.time0, self.time3, 4, 2],
                                            '106.120.173.jie': [self.time2, self.time2, 1, 1],
                                            '107.178.195.aag': [self.time2, self.time2, 1, 2]})
        self.assertDictEqual(expiration_dict, {self.time4: ['106.120.173.jie', '107.178.195.aag'],
                                               self.time5: ['107.23.85.jfd']})

    def test_write_remaining_sessions(self):
        request_dict = {'107.23.85.jfd': [self.time0, self.time3, 4, 2],
                        '106.120.173.jie': [self.time2, self.time2, 1, 1],
                        '107.178.195.aag': [self.time2, self.time4, 2, 2],
                        '108.91.91.hbc': [self.time4, self.time4, 1, 1]}
        expiration_dict = {self.time4: ['106.120.173.jie', '107.178.195.aag'],
                           self.time5: ['107.23.85.jfd'],
                           self.time6: ['107.178.195.aag']}
        output_handle = StringIO()
        sessionize.write_remaining_sessions(output_handle, request_dict, expiration_dict)
        self.assertEqual(output_handle.getvalue(), '107.23.85.jfd,2017-06-30 00:00:00,2017-06-30 00:00:03,4,4\n' +
                                                   '106.120.173.jie,2017-06-30 00:00:02,2017-06-30 00:00:02,1,1\n' +
                                                   '107.178.195.aag,2017-06-30 00:00:02,2017-06-30 00:00:04,3,2\n' +
                                                   '108.91.91.hbc,2017-06-30 00:00:04,2017-06-30 00:00:04,1,1\n')
        self.assertDictEqual(request_dict, {})
        self.assertDictEqual(expiration_dict, {})

    def test_process_data_stream(self):
        input_handle = StringIO('ip,date,time,zone,cik,accession,extention,code,size,idx,norefer,noagent,find,crawler,browser\n' +
                                '101.81.133.jja,2017-06-30,00:00:00,0.0,1608552.0,0001047469-17-004337,-index.htm,200.0,80251.0,1.0,0.0,0.0,9.0,0.0,\n' +
                                '107.23.85.jfd,2017-06-30,00:00:00,0.0,1027281.0,0000898430-02-001167,-index.htm,200.0,2825.0,1.0,0.0,0.0,10.0,0.0,\n' +
                                '107.23.85.jfd,2017-06-30,00:00:00,0.0,1136894.0,0000905148-07-003827,-index.htm,200.0,3021.0,1.0,0.0,0.0,10.0,0.0,\n' +
                                '107.23.85.jfd,2017-06-30,00:00:01,0.0,841535.0,0000841535-98-000002,-index.html,200.0,2699.0,1.0,0.0,0.0,10.0,0.0,\n' +
                                '108.91.91.hbc,2017-06-30,00:00:01,0.0,1295391.0,0001209784-17-000052,.txt,200.0,19884.0,0.0,0.0,0.0,10.0,0.0,\n' +
                                '106.120.173.jie,2017-06-30,00:00:02,0.0,1470683.0,0001144204-14-046448,v385454_20fa.htm,301.0,663.0,0.0,0.0,0.0,10.0,0.0,\n' +
                                '107.178.195.aag,2017-06-30,00:00:02,0.0,1068124.0,0000350001-15-000854,-xbrl.zip,404.0,784.0,0.0,0.0,0.0,10.0,1.0,\n' +
                                '107.23.85.jfd,2017-06-30,00:00:03,0.0,842814.0,0000842814-98-000001,-index.html,200.0,2690.0,1.0,0.0,0.0,10.0,0.0,\n' +
                                '107.178.195.aag,2017-06-30,00:00:04,0.0,1068124.0,0000350001-15-000731,-xbrl.zip,404.0,784.0,0.0,0.0,0.0,10.0,1.0,\n' +
                                '108.91.91.hbc,2017-06-30,00:00:04,0.0,1618174.0,0001140361-17-026711,.txt,301.0,674.0,0.0,0.0,0.0,10.0,0.0,\n')

        output_handle = StringIO()

        inactivity_handle = StringIO('2\n')

        sessionize.process_data_stream(input_handle, inactivity_handle, output_handle)
        self.assertEqual(output_handle.getvalue(), '101.81.133.jja,2017-06-30 00:00:00,2017-06-30 00:00:00,1,1\n' +
                                                   '108.91.91.hbc,2017-06-30 00:00:01,2017-06-30 00:00:01,1,1\n' +
                                                   '107.23.85.jfd,2017-06-30 00:00:00,2017-06-30 00:00:03,4,4\n' +
                                                   '106.120.173.jie,2017-06-30 00:00:02,2017-06-30 00:00:02,1,1\n' +
                                                   '107.178.195.aag,2017-06-30 00:00:02,2017-06-30 00:00:04,3,2\n' +
                                                   '108.91.91.hbc,2017-06-30 00:00:04,2017-06-30 00:00:04,1,1\n')
        output_handle = StringIO()
        input_handle.seek(0)
        inactivity_handle = StringIO('1\n')
        sessionize.process_data_stream(input_handle, inactivity_handle, output_handle)
        self.assertEqual(output_handle.getvalue(), '101.81.133.jja,2017-06-30 00:00:00,2017-06-30 00:00:00,1,1\n' +
                                                   '107.23.85.jfd,2017-06-30 00:00:00,2017-06-30 00:00:01,2,3\n' +
                                                   '108.91.91.hbc,2017-06-30 00:00:01,2017-06-30 00:00:01,1,1\n' +
                                                   '106.120.173.jie,2017-06-30 00:00:02,2017-06-30 00:00:02,1,1\n' +
                                                   '107.178.195.aag,2017-06-30 00:00:02,2017-06-30 00:00:02,1,1\n' +
                                                   '107.23.85.jfd,2017-06-30 00:00:03,2017-06-30 00:00:03,1,1\n' +
                                                   '107.178.195.aag,2017-06-30 00:00:04,2017-06-30 00:00:04,1,1\n' +
                                                   '108.91.91.hbc,2017-06-30 00:00:04,2017-06-30 00:00:04,1,1\n')

        output_handle = StringIO()
        input_handle.seek(0)
        inactivity_handle = StringIO('3\n')
        sessionize.process_data_stream(input_handle, inactivity_handle, output_handle)
        self.assertEqual(output_handle.getvalue(), '101.81.133.jja,2017-06-30 00:00:00,2017-06-30 00:00:00,1,1\n' +
                                                   '107.23.85.jfd,2017-06-30 00:00:00,2017-06-30 00:00:03,4,4\n' +
                                                   '108.91.91.hbc,2017-06-30 00:00:01,2017-06-30 00:00:04,4,2\n' +
                                                   '106.120.173.jie,2017-06-30 00:00:02,2017-06-30 00:00:02,1,1\n' +
                                                   '107.178.195.aag,2017-06-30 00:00:02,2017-06-30 00:00:04,3,2\n')

        output_handle = StringIO()
        input_handle.seek(0)
        inactivity_handle = StringIO('4\n')
        sessionize.process_data_stream(input_handle, inactivity_handle, output_handle)
        self.assertEqual(output_handle.getvalue(), '101.81.133.jja,2017-06-30 00:00:00,2017-06-30 00:00:00,1,1\n' +
                                                   '107.23.85.jfd,2017-06-30 00:00:00,2017-06-30 00:00:03,4,4\n' +
                                                   '108.91.91.hbc,2017-06-30 00:00:01,2017-06-30 00:00:04,4,2\n' +
                                                   '106.120.173.jie,2017-06-30 00:00:02,2017-06-30 00:00:02,1,1\n' +
                                                   '107.178.195.aag,2017-06-30 00:00:02,2017-06-30 00:00:04,3,2\n')

        output_handle = StringIO()
        input_handle.seek(0)
        inactivity_handle = StringIO('0\n')
        with self.assertRaises(Exception):
            sessionize.process_data_stream(input_handle, inactivity_handle, output_handle)

        output_handle = StringIO()
        input_handle.seek(0)
        inactivity_handle = StringIO('86401\n')
        with self.assertRaises(Exception):
            sessionize.process_data_stream(input_handle, inactivity_handle, output_handle)

    def test_get_inactivity_interval(self):
        inactivity_handle = StringIO('0\n')
        with self.assertRaises(Exception):
            sessionize.get_inactivity_interval(inactivity_handle)

        inactivity_handle = StringIO('86401\n')
        with self.assertRaises(Exception):
            sessionize.get_inactivity_interval(inactivity_handle)

        inactivity_handle = StringIO('1\n')
        self.assertEqual(sessionize.get_inactivity_interval(inactivity_handle), 1)

        inactivity_handle = StringIO('3\n')
        self.assertEqual(sessionize.get_inactivity_interval(inactivity_handle), 3)

        inactivity_handle = StringIO('86400\n')
        self.assertEqual(sessionize.get_inactivity_interval(inactivity_handle), 86400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
