import os
import uuid
from flask import Flask, request, jsonify, send_file
from argparse import ArgumentParser
from noteshrink import notescan_main

# This adds the MessyDeskAPI endpoint to noteshrink
# https://github.com/mzucker/noteshrink


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

OUTPUT_FOLDER = 'output'
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


@app.route('/process', methods=['POST'])
def process_files():
    # Check if files are present in the request
    if 'request' not in request.files or 'content' not in request.files:
        return jsonify({'error': 'JSON file and image file are required'}), 400
    
    json_file = request.files['request']
    image_file = request.files['content']

    # Check if the file is empty
    if json_file.filename == '' or image_file.filename == '':
        return jsonify({'error': 'Empty file submitted'}), 400

    # Read JSON file
    try:
        json_data = json_file.read().decode('utf-8')
        # You can parse JSON data here if needed
    except Exception as e:
        return jsonify({'error': 'Failed to read JSON file: {}'.format(str(e))}), 400

    # Save image file with original extension
    try:
        output_id = str(uuid.uuid4())
        image_filename, image_extension = os.path.splitext(image_file.filename)
        image_path = os.path.join(UPLOAD_FOLDER, output_id + image_extension)
        image_file.save(image_path)
        filenames = [image_path]
        args = get_argument_parser(os.path.join(OUTPUT_FOLDER, output_id)).parse_args(['dummy_script.py'] + filenames)

        # call noteshrink
        notescan_main(args)


    except Exception as e:
        return jsonify({'error': 'Failed to save image file: {}'.format(str(e))}), 500

    return jsonify({'response':{'type': 'stored', 'uri': ['/files/' + output_id + '.png']}}), 200


# endpoint to serve files
@app.route('/files/<path:filename>', methods=['GET'])       
def serve_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.isfile(file_path):
        return send_file(file_path)
    else:
        return jsonify({'error': 'File not found'}), 404

def get_argument_parser(basename):

    '''Parse the command-line arguments for this program.'''

    parser = ArgumentParser(
        description='convert scanned, hand-written notes to PDF')

    show_default = ' (default %(default)s)'

    parser.add_argument('filenames', metavar='IMAGE', nargs='+',
                        help='files to convert')

    parser.add_argument('-q', dest='quiet', action='store_true',
                        default=False,
                        help='reduce program output')

    parser.add_argument('-b', dest='basename', metavar='BASENAME',
                        default=basename,
                        help='output PNG filename base' + show_default)

    parser.add_argument('-o', dest='pdfname', metavar='PDF',
                        default='output.pdf',
                        help='output PDF filename' + show_default)

    parser.add_argument('-v', dest='value_threshold', metavar='PERCENT',
                        type=percent, default='25',
                        help='background value threshold %%'+show_default)

    parser.add_argument('-s', dest='sat_threshold', metavar='PERCENT',
                        type=percent, default='20',
                        help='background saturation '
                        'threshold %%'+show_default)

    parser.add_argument('-n', dest='num_colors', type=int,
                        default='8',
                        help='number of output colors '+show_default)

    parser.add_argument('-p', dest='sample_fraction',
                        metavar='PERCENT',
                        type=percent, default='5',
                        help='%% of pixels to sample' + show_default)

    parser.add_argument('-w', dest='white_bg', action='store_true',
                        default=False, help='make background white')

    parser.add_argument('-g', dest='global_palette',
                        action='store_true', default=False,
                        help='use one global palette for all pages')

    parser.add_argument('-S', dest='saturate', action='store_false',
                        default=True, help='do not saturate colors')

    parser.add_argument('-K', dest='sort_numerically',
                        action='store_false', default=True,
                        help='keep filenames ordered as specified; '
                        'use if you *really* want IMG_10.png to '
                        'precede IMG_2.png')

    parser.add_argument('-P', dest='postprocess_cmd', default=None,
                        help='set postprocessing command (see -O, -C, -Q)')

    parser.add_argument('-e', dest='postprocess_ext',
                        default='_post.png',
                        help='filename suffix/extension for '
                        'postprocessing command')

    parser.add_argument('-O', dest='postprocess_cmd',
                        action='store_const',
                        const='optipng -silent %i -out %o',
                        help='same as -P "%(const)s"')

    parser.add_argument('-C', dest='postprocess_cmd',
                        action='store_const',
                        const='pngcrush -q %i %o',
                        help='same as -P "%(const)s"')

    parser.add_argument('-Q', dest='postprocess_cmd',
                        action='store_const',
                        const='pngquant --ext %e %i',
                        help='same as -P "%(const)s"')

    parser.add_argument('-c', dest='pdf_cmd', metavar="COMMAND",
                        default='convert %i %o',
                        help='PDF command (default "%(default)s")')

    return parser

def percent(string):
    '''Convert a string (i.e. 85) to a fraction (i.e. .85).'''
    return float(string)/100.0

if __name__ == '__main__':
    app.run(debug=True)

