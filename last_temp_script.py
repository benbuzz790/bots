import sys
import traceback


def main():
    import subprocess
    try:
        result = subprocess.run(['python', 'test_bots.py'], capture_output=
            True, text=True, timeout=60)
        print('Test Results:')
        print(result.stdout)
        if result.stderr:
            print('Errors:')
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print('Error: Test execution timed out.')
    except Exception as e:
        print(f'Error: {str(e)}')


if __name__ == '__main__':
    try:
        main()
    except Exception as error_error:
        print(f'An error occurred: {str(error_error)}', file=sys.stderr)
        print('Local variables at the time of the error:', file=sys.stderr)
        tb = sys.exc_info()[2]
        while tb:
            frame = tb.tb_frame
            tb = tb.tb_next
            print(
                f'Frame {frame.f_code.co_name} in {frame.f_code.co_filename}:{frame.f_lineno}'
                , file=sys.stderr)
            local_vars = dict(frame.f_locals)
            for key, value in local_vars.items():
                if not key.startswith('__') and key not in ['sys',
                    'traceback', 'error_error', 'main', 'tb', 'frame', 'Frame'
                    ]:
                    print(f'    {key} = {value}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)