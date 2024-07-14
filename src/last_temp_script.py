import sys
import traceback


def main():
    import os
    import shutil
    os.makedirs('src', exist_ok=True)
    os.makedirs('tests', exist_ok=True)
    for file in os.listdir('.'):
        if file.endswith('_test.py'):
            shutil.move(file, os.path.join('tests', file))
        elif file.endswith('.py') and not file.startswith('test_'):
            shutil.move(file, os.path.join('src', file))
        elif file in ['requirements.txt', 'README.md']:
            pass
        else:
            print(f'Not sure where to put {file}, leaving it in root.')
    print('Reorganization complete. New structure:')
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 4 * level
        print(f'{indent}{os.path.basename(root)}/')
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            print(f'{sub_indent}{f}')


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