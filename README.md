# Table of Content
1. [Running the Code](README.md#running-the-Code)
2. [Assumptions](README.md#assumptions)
3. [Output File Format](README.md#output-file-format)
4. [A Short Description of the Code](README.md#a-short-description-of-the-code)
5. [Code Requirements and Testing](README.md#code-requirements-and-testing)


# Extracting Sessions from an EDGAR Log File
## Running the Code
The command format for running the code is:

```python ./src/sessionization.py ./input/log.csv ./input/inactivity_period.txt ./output/sessionization.txt```

Obviously the name or path of the files can be different from above. However, the order should be the same, meaning that the first file is the main python code. The second file is the input data in the format described by [FEC](https://www.sec.gov/dera/data/edgar-log-file-data-set.html) for Electronic Data Gathering, Analysis, and Retrieval (EDGAR) [log files](https://www.sec.gov/dera/data/edgar-log-file-data-set.html). The third file contains the inactivity value in seconds after which a session expires. The fourth file is the output file.

There is an optional parameter `-time` that if needed should be entered as the fifth input argument: 

```python ./src/sessionization.py ./input/log.csv ./input/inactivity_period.txt ./output/sessionization.txt -time```

If provided, the code prints the run time at the end of each run.

## Assumptions
- Data is written or streams chronologically in the input file.
- Input data is in the format described by [FEC](https://www.sec.gov/files/EDGAR_variables_FINAL.pdf) for EDGAR log files.
- The header (first line of input file) specifies the order of variables in that input file.
- Required fields for this program are `ip`, `date`, `time`, `cik`, `accession`, `extention`.
- Fields can be ordered in any way seperated by comma as long as all required fields are present and they follow the ordering of the header.
- Inactivity interval value is assumed to be between 1 and 86,400 seconds (inclusive).
- Duration of a session is inclusive, i.e. if the start time is 2017-06-30 00:00:00 and the end time is 2017-06-30 00:00:05, the duration is 6 seconds.
- Code skips a record if ip field is empty.
- If the record does not have enough fields to match the required fields, the record will be skipped.
- If date-time field does not conform to '%Y-%m-%d %H:%M:%S' format which is 'YYYY-mm-dd HH-MM-SS', the code tries to use latest date-time read from the stream. Only if it is the first record and it does not conform the mentioned format, the record would be skipped.
- A session starts the first time we see a request from a specific ip, which is equivalent to a unique user here. That session ends if we don't see any request from that ip for equal or more than inactivity interval.

## Output File Format
Output file format is:

```ip,session_start_date_time,session_end_date_time,session_duration_in_seconds,number_of_requested_documents```

Both `session_start_date_time` and `session_end_date_time` are formatted as `%Y-%m-%d %H:%M:%S`. Each line represent one record. For each session in the input file which also depend on the inactivity interval value, a corresponding output line will be written.

## A Short Description of the Code
This code parse the input file line by line and write the output in the output file. This way it avoids the requirement to load all the input data, specially since the input file can be very large in size. The code assume chronoligical appearance of records and at each time writes the records first in order of their start time and then in order of their appearance if the start time of two records are the same. Consequently, the behavior of the code is affected by this design. It means that if the order of information in the input file changes, the resulting output can be different. 

To store the open session, and make the retrieval of their information O(1), a dictionary, `request_dict`, is used here in which the key is the ip address and the value is a list: 

- `request_dict[ip] = [start_date_time_of_session, end_date_time_of session, number_of_docs_requested, time_specific_unique_counter]`. 
- When an ip is not in the dictionary, `start_date_time_of_session` and `end_date_time_of_session` will be set as time of the current request (stored as datetime objects) and `number_of_docs_requested` sets to 1. 
- `time_specific_unique_counter` is a counter which remains unique for all the records that have the same time stamp and is used to order the output correctly when two expired session has the same starting time. `time_specific_unique_counter` is set when a session starts and will not be modified later. 
- When ip is in the dictionary, `end_date_time_of_session` is set to the datetime of current record and `number_of_docs_requested` will be increased by 1.

At each time we need to find out which sessions are expired and write them to the output. To do so another dictionary, `expiration_dict`, is used which keeps a set of ip addresses of sessions that might expire at a specific time. Whenever a record is read, its ip field is added to the expiration record. The key to this dictionary is a datetime object with a date_time equal `current_record_date_time + inactivity_interval`, which is a potential expiration time of current record if no request from this ip is seen until expiration time. After all records from the current_time is read, all the ips in the set of potential expiring sessions will be checked. If they are expired, they will be written to the output file. To make order of output correct, the potential expiration set is converted to a list and first ordered by the `start_time_of_session` and then by the `time_specific_unique_counter`. Whenever a session is expired, it will be removed from the request_dict.

When the end of input file is reached, all the remaining records in the `request_dict` will be written to the output file ordered first by the `start_time_of_session` and then by the `time_specific_unique_counter`.

## Code Requirements and Testing
I have tested the code with python 3.5.3 and it needs the following modules: `sys`, `datetime`, and `time`.

I have also written some unittests for the functions in the `./src/sessionization.py`. You can find the tests in `./src/test_sessionization.py`. To run those tests you can simply execute:

```python ./src/test_analyse_repeat_donations.py```

The tests are written using the `unittest` module.

There are also a few integration tests in the folder `./insight_testsuite/tests/`. You can run those tests by running this shell script: `./insight_testsuite/run_tests.sh`.






