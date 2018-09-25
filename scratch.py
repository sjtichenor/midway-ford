import os


for filename in os.listdir('/Users/spencertichenor/Drive/Pictures/sales-specials-images'):

    if filename.endswith('copy.jpg'):
        file_path = '/Users/spencertichenor/Drive/Pictures/sales-specials-images/' + filename
        new_file_name = '/Users/spencertichenor/Drive/Pictures/sales-specials-images/' + filename.replace(' copy', '')
        os.rename(file_path, new_file_name)


