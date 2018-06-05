import sys
import time
from datetime import timedelta
from datetime import datetime


def open_files(file_list):
    """
        Opens all the files in the file list and return their handles.
    :param file_list: a list consisting a tuple for each file to be opened.
                      tuple has the form (file_path, file_opening_mode)
    :return: a tuple of file handles with the same order as the tuples in the file_list
    """
    f_handles = ()
    for file_item in file_list:
        file_path, opening_mode = file_item
        try:
            f_handles += (open(file_path, opening_mode),)
        except OSError:
            print('An error occurred while opening file: ', file_path)
            sys.exit()

    return f_handles


def close_files(file_handle_list):
    """
        Closes all file provided in the file_handle_list.
    :param file_handle_list: a list of file handles.
    """
    for file in file_handle_list:
        try:
            file.close()
        except:
            print('An error occurred while closing files.')
            raise


def check_field_validity_and_cleanup(ip, d, t, cik, accession, extention, last_date_time=None):
    """
        Returns a tuple (validity, fields). If any of the provided fields are malformed or incorrect, it returns False
        for validity and an empty list for fields. If all fields are valid it cleans up the
        fields and returns them. It also converts d and t to a datetime object.
        Cleanups include: striping white spaces from beginning and end of fields and returning the last_date_time in
        case the d or t are not in the right format and a last_date_time is provided.

    :param ip: ip of the user as string
    :param d: date of request as string with YYYY-MM-DD format
    :param t: time of request as string with hh:mm:ss format
    :param cik: cik field of request as string
    :param accession: accession field of request as string
    :param extention: extention field of request as string
    :param last_date_time: last_date_time seen from the data stream as datetime object
    :return: a tuple in this form (is_valid, (ip, datetime_obj, cik, accession, extention))
    """

    # white space stripping and checks
    ip = ip.strip()
    if ip == '':
        return False, ()

    try:
        datetime_obj = datetime.strptime(d + ' ' + t, '%Y-%m-%d %H:%M:%S')
    except:
        # if datetime is not in the right format but we know the latest time read from data stream, use that otherwise
        # mark the record as invalid
        if last_date_time:
            datetime_obj = last_date_time
        else:
            return False, ()

    cik = cik.strip()
    accession = accession.strip()
    extention = extention.strip()

    is_valid = True      # no field-check failed
    return is_valid, (ip, datetime_obj, cik, accession, extention)


def extract_required_fields(record_string, req_fields):
    """
        Extract all the fields from a record_string which is raw record with fields separated by comma
        and return required fields.

    :param record_string: raw record for a document request according to FEC description
    :param req_fields: a dictionary containing required fields as key and the index of that field in the comma seperated
                        record as value.
    :return: the required fields as a tuple (ip, date, time, cik, accession, extention)
    """

    all_fields = record_string.split(',')

    try:
        extracted_fields = (all_fields[req_fields[key]]
                            for key in ['ip', 'date', 'time', 'cik', 'accession', 'extention'])
    except: # if the record does not match header format a tuple with empty fields is returned which will be skipped
        ('', '', '', '', '', '')

    return extracted_fields


def extract_required_fields_order(header, required_fields):
    """
        Extract the all the required fields from the header which is the name of fields separated by comma
        and return required fields.

    :param header: a comma seperated string including list of fields
    :param required_fields: a list containing name of required fields
    :return: a tuple including order of required fields in the header or a line of input data  (zero-indexed)
    """
    all_fields = header.split(',')
    required_fields_order = ()
    for field in required_fields:
        for i, x in enumerate(all_fields):
            if field == x:
                required_fields_order += (i,)

    if len(required_fields_order) != len(required_fields):
        raise Exception('Some of required fields are not found in the header.')

    return required_fields_order


def write_closed_sessions(output_handle, date_time, previous_date_time, inactivity_interval, request_dict,
                          expiration_dict):
    """
        Checks the sessions which might have expired at date_time and if so writes them out to the output file.
        The output form is:
           'ip,session_start_date_time,session_end_date_time,session_duration_in_seconds,number_of_requested_documents'
        where date_time is written in this format: YYYY-MM-DD hh:mm:ss

    :param output_handle: output file handle
    :param date_time: a datetime object indicating the expiration time to check
    :param previous_date_time: a date_time before current date_time in the code in general
                            previous_date_time <= date_time < current_date_time
    :param inactivity_interval: inactivity interval in seconds after which a session is considered as expired
    :param request_dict: a dictionary containing all the documents request seen up to now with ip as key and
                        [start date_time of session, end date_time of session, number of docs requested,
                        a unique counter showing order of appearance in the same start date_time] as value
    :param expiration_dict: a dictionary containing the sessions that might get expired at a specific datetime. The key
                            is expiration datetime and the value is a set of ip address of sessions that might get
                            expired at the time specified by key.
    :return: None
    """
    i = 0
    while True:
        date_time_to_chck = previous_date_time + timedelta(seconds=i)   # this is to make sure that if a gap of time is
                                                                        # in request the code does not miss some entries
                                                                        # in expiration_dict
        if date_time_to_chck <= date_time and date_time_to_chck in expiration_dict:
            potential_expiring_sessions = sorted(expiration_dict[date_time_to_chck],
                                                  key=lambda r: (request_dict[r][0], request_dict[r][3]))
            for ip in potential_expiring_sessions:
                # check if the session with ip has expired and write it to output file if so
                if request_dict[ip][1] <= date_time_to_chck - timedelta(seconds=inactivity_interval):
                    session_info = request_dict.pop(ip)
                    record = [ip,
                              session_info[0].isoformat(' '),
                              session_info[1].isoformat(' '),
                              str(int((session_info[1] - session_info[0]).total_seconds()) + 1),
                              str(session_info[2])]
                    output_handle.write(','.join(record) + '\n')

            expiration_dict.pop(date_time_to_chck)
        elif date_time_to_chck > date_time:
            break
        i += 1


def write_remaining_sessions(output_handle, request_dict, expiration_dict):
    """
        Writes all the sessions in request_dict to the output file. The output is ordered first by start_time of
        sessions and if two sessions are started at the same time, the unique counter for that time is used to order
        those sessions. The output form is:
           'ip,session_start_date_time,session_end_date_time,session_duration_in_seconds,number_of_requested_documents'
        where date_time is written in this format: YYYY-MM-DD hh:mm:ss

    :param output_handle: output file handle
    :param request_dict: a dictionary containing all the documents request seen up to now with ip as key and
                        [start date_time of session, end date_time of session, number of docs requested,
                        a unique counter showing order of appearance in the same start date_time] as value
    :param expiration_dict: a dictionary containing the sessions that might get expired at a specific datetime. The key
                            is expiration datetime and the value is a set of ip address of sessions that might get
                            expired at the time specified by key.
    :return: None
    """

    for ip in sorted(request_dict.keys(), key=lambda r: (request_dict[r][0], request_dict[r][3])):
        # write the sessions ordered by start_time and unique counter when start_times are equal
        session_info = request_dict.pop(ip)
        record = [ip,
                  session_info[0].isoformat(' '),
                  session_info[1].isoformat(' '),
                  str(int((session_info[1] - session_info[0]).total_seconds()) + 1),
                  str(session_info[2])]
        output_handle.write(','.join(record) + '\n')

    expiration_dict.clear()


def get_order_of_required_fields(input_handle):
    """
        Reads the header of the input file (first line of inout file) and extract the order of required fields:
                            'ip', 'date', 'time', 'cik', 'accession', 'extention'
    :param input_handle: file handle for the input file
    :return: a dictionary with name of required fields as the key and their index of appearance in the records as value
    """

    first_line = input_handle.readline()
    required_fields_names = ['ip', 'date', 'time', 'cik', 'accession', 'extention']
    fields_order = extract_required_fields_order(first_line, required_fields_names)
    req_fields = dict(zip(required_fields_names, fields_order))
    return req_fields


def get_inactivity_interval(inactivity_handle):
    """
        Reads the inactivity interval from the inactivity input file.
        Assume 1 second <= inactivity_interval <= 86400 seconds
    :param inactivity_handle: file handle for inactivity input file
    :return: inactivity interval in seconds
    """
    # read the inactivity interval
    first_line = inactivity_handle.readline()  # assume the inactivity interval is at the first line
    inactivity_interval = int(first_line.strip())
    if inactivity_interval < 1 or inactivity_interval > 86400:
        raise ValueError('The provided interval should be between 1 and 86,400.')

    return inactivity_interval


def process_data_stream(input_handle, inactivity_handle, output_handle):
    """
        This function process a data_stream of EDGAR records by reading from input_handle that is formatted based on FEC
        description. It uses the inactivity interval that is supposed to be in the first line of inactivity_file and
        write to the output_file which will contains the following information regarding each user session: ip address
        of that user, date and time of the first webpage request in the session, date and time of the last webpage
        request in the session, duration of the session in seconds, and count of webpage requests during the session.
    :param input_handle: file handle for the input file.
    :param inactivity_handle: file handle for the inactivity interval file.
    :param output_handle: file handle for the output file
    """

    inactivity_interval = get_inactivity_interval(inactivity_handle)

    req_fields = get_order_of_required_fields(input_handle)

    request_dict = {}
    expiration_dict = {}
    latest_date_time = None     # latest time seen
    previous_date_time = None   # previous time seen, almost always (except when reading first second) is not the same
                                # as latest_date_time and is at least 1 second smaller than latest_date_time
    counter = 0

    for line in input_handle:
        (ip, d, t, cik, accession, extention) = extract_required_fields(line, req_fields)
        (is_valid, fields) = check_field_validity_and_cleanup(ip, d, t, cik, accession, extention, latest_date_time)
        if not is_valid:  # skip this record if any of the required fields are not valid
            continue

        (ip, date_time, cik, accession, extention) = fields

        # when time changes check the potential session that might expire and write them if so
        if previous_date_time is not None and date_time > previous_date_time:
            write_closed_sessions(output_handle, date_time - timedelta(seconds=1), previous_date_time,
                                  inactivity_interval, request_dict, expiration_dict)

        # update a counter which is set to zero when time changes and
        if previous_date_time is None or date_time > latest_date_time:
            counter = 0
        else:
            counter += 1
        if ip in request_dict:
            request_dict[ip][1] = date_time  # update end date_time of session
            request_dict[ip][2] += 1         # increase number of docs requested by one
        else:
            # add this ip (user) to request dictionary
            request_dict[ip] = [date_time, date_time, 1, counter]   # [start date_time of session, end date_time of
                                                                    #  session, number of docs requested, a unique
                                                                    #  counter that differentiates order of appearance
                                                                    #  at a specific time]
        # update the expiration dictionary
        exp_time = date_time + timedelta(seconds=inactivity_interval)
        if exp_time in expiration_dict:
            expiration_dict[exp_time].add(ip)
        else:
            expiration_dict[exp_time] = {ip}
        # update previous_date_time
        if previous_date_time is None or date_time > latest_date_time:
            previous_date_time = date_time
        latest_date_time = date_time

    # since the input file end is reached, write all the remaining sessions
    write_remaining_sessions(output_handle, request_dict, expiration_dict)


if __name__ == "__main__":
    # if optional -time argument is entered, time the code
    if len(sys.argv) >= 5 and sys.argv[4] == '-time':
        start_time = time.time()

    # get the location of input and output file from command line
    try:
        input_path = sys.argv[1]
        inactivity_path = sys.argv[2]
        output_path = sys.argv[3]
    except:
        raise Exception(('You need to enter the following paths as command arguments: input_file, inactivity_file, ',
                        'and output_file!'))

    file_handles = open_files([(input_path, 'r'), (inactivity_path, 'r'), (output_path, 'w')])
    input_handle, inactivity_handle, output_handle = file_handles

    process_data_stream(input_handle, inactivity_handle, output_handle)

    close_files([input_handle, inactivity_handle, output_handle])

    # if optional -time argument is entered, print the run time
    if len(sys.argv) >= 5 and sys.argv[4] == '-time':
        print("--- running time: %s seconds ---" % (time.time() - start_time))
