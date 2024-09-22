import os
import sys
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    import os
    import codecs

    def remove_bom_from_files():

        def remove_bom(file_path):
            with open(file_path, 'rb') as file:
                content = file.read()
            if content.startswith(codecs.BOM_UTF8):
                with open(file_path, 'wb') as file:
                    file.write(content[len(codecs.BOM_UTF8):])
                print(f'Removed BOM from: {file_path}')
            else:
                print(f'No BOM found in: {file_path}')
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    remove_bom(file_path)
                except Exception as e:
                    print(f'Error processing {file_path}: {str(e)}')
        print('BOM removal process completed.')
    remove_bom_from_files()


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
                    'traceback', 'error_error', 'main', 'tb', 'frame']:
                    print(f'    {key} = {value}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
