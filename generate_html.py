import os
import glob
import json


def to_html(root, html_name, sort_key):
    '''
    Args:
        root (str): Directory with all the files with following directory structure:
            vis_dir/
            ├── ClosedSet
            │   ├── avatasnet
            │   │   ├── ex_54
            │   │   │   ├── metrics.json
            │   │   │   ├── mixture.wav
            │   │   │   ├── s0_estimate.wav
            │   │   │   ├── s0.wav
            |   |   |   |...
            │   │   │   ├── s{k}_estimate.wav
            │   │   │   └── s{k}.wav
            |   |   |...
            |   |...
            ├── OpenSet
            │   ├── acadptnet
            │   │   ├── ex_54
            │   │   │   ├── metrics.json
            │   │   │   ├── mixture.wav
            │   │   │   ├── s0_estimate.wav
            │   │   │   ├── s0.wav
            |   |   |   |...
            │   │   │   ├── s{k}_estimate.wav
            │   │   │   └── s{k}.wav
            |   |   |...
            |   |...
        html_name (str): name of HTML file to be stored without .html
        sort_key (dict): model names for sorting according to Si-SDR
            Dictionary should have keys "ClosedSet" and "OpenSet"
            with values as the model folder names.
    '''
    visualizer = HTMLVisualizer(f'{html_name}.html')

    # Check OpenSet and ClosedSet
    sets_present = []
    for folder in os.listdir(root):
        if folder=="OpenSet" and len(os.listdir(root+"/OpenSet"))>0:
            sets_present.append("OpenSet")
        elif folder=="ClosedSet" and len(os.listdir(root+"/ClosedSet"))>0:
            sets_present.append("ClosedSet")

    # Add page links
    visualizer.add_sets(sets_present)

    # Loop over sets
    for set_ in sets_present:
        set_dir = root+"/"+set_
        models_present = os.listdir(set_dir) # Check Models present
        if len(models_present)>0:
            # Create subpage
            visualizer.add_div(set_)

            # init headers
            header = ['Filename', 'Mixture Audio', 'Ground Truth']

            # Check number of sources
            model0_files = os.listdir(set_dir+"/"+models_present[0])
            model0_ex0_path = set_dir+"/"+models_present[0]+"/"+model0_files[0]
            num_sources = len(glob.glob(model0_ex0_path+"/s*_estimate.wav"))

            for model in models_present:
                header.append(model)
            visualizer.add_header(header)

            # init rows
            vis_rows = []
            # get examples
            dirs = glob.glob(f'{root}/{set_}/{models_present[0]}/ex_*')
            example_nums = [ex.split('/')[-1] for ex in dirs]

            # Add rows
            vis_rows = []
            for ex in example_nums:
                row_elements = [('num_sources', num_sources), ('num_models', len(models_present))]
                # get mixture from first model
                with open(f'{root}/{set_}/{models_present[0]}/{ex}/metrics.json', 'r') as fp:
                    metrics = json.load(fp)
                    mixture_name = metrics['mix_path'].split('/')[-1].replace('.wav', '').replace('_', ' v.s. ')
                    fp.close()
                row_elements.append( ('mixture_name', mixture_name) )
                # get mixture audio from first model
                row_elements.append( ('mixture_path', f'{root}/{set_}/{models_present[0]}/{ex}/mixture.wav') )

                for i in range(num_sources):
                    # get ground truth from first model
                    if i>0:
                        row_elements.append( ('change_row', None) )
                    row_elements.append( ('audio', f'{root}/{set_}/{models_present[0]}/{ex}/s{i}.wav') )
                    for model in models_present:
                        with open(f'{root}/{set_}/{model}/{ex}/metrics.json', 'r') as fp:
                            metrics = json.load(fp)
                            row_elements.append( ('text_sisdr', metrics['si_sdr']) )
                            fp.close()
                        row_elements.append( ('estimate_audio', f'{root}/{set_}/{model}/{ex}/s{i}_estimate.wav') )

                vis_rows.append(row_elements)

            # Sorting
            set_sort_key = sort_key[set_]
            sort_dirs = glob.glob(f'{root}/{set_}/{set_sort_key}/ex_*')
            sisdrs = []
            for dd in sort_dirs:
                with open(f'{dd}/metrics.json', 'r') as fp:
                    metrics = json.load(fp)
                    sisdrs.append(metrics['si_sdr'])
                    fp.close()
            # sort by si_sdr
            vis_rows = [x for _,x in sorted(zip(sisdrs, vis_rows), reverse=False)]

            visualizer.add_rows(vis_rows)
            visualizer.close_div()
    visualizer.write_html()


class HTMLVisualizer():
    def __init__(self, fn_html):
        self.fn_html = fn_html
        self.content = '<!DOCTYPE html> <html>' # Add HTML tag
        self.content += '<head><title>Audio Source Separation</title></head>' # Add title
        self.content += '<body>' # Add body tag
        self.content += '<center><h1>Audio Source Separation</h1></center>' # Add heading

    def add_sets(self, sets_present):
        for set_ in sets_present:
            self.content += '<center><p><a href="#{}">{}</a></p></center>'.format(set_.lower(), set_)

    def add_div(self, set_):
        self.content += '<div class="page" id="{}">'.format(set_.lower())
        self.content += '<center><h2>{}</h2></center>'.format(set_)
        self.content += '<center>'
        self.content += "<table>"
        self.content += '<style> table, \
        th, \
        td {border: 1px solid black;}, \
        table {width: 100% !important;}, \
        audio {width: 220px; display: block;}, \
        </style>'

    def close_div(self):
        self.content += '</table>'
        self.content += '</center>'
        self.content += '</div>'

    def add_header(self, elements):
        self.content += '<tr>'
        for element in elements:
            self.content += '<th>{}</th>'.format(element)
        self.content += '</tr>'

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def add_row(self, elements):
        self.content += '<tr>'

        # get important variables
        for element in elements:
            if element[0] == 'mixture_name':
                mixture_name = element[1]
            elif element[0] == 'num_sources':
                num_sources = element[1]
            elif element[0] == 'num_models':
                num_models = element[1]
            elif element[0] == 'mixture_path':
                mixture_path = element[1]

        # add mixture name
        self.content += '<td rowspan="{}">'.format(num_sources)
        self.content += mixture_name
        self.content += '</td>'

        # add mixture audio
        self.content += '<td rowspan="{}">'.format(num_sources)
        self.content += '<audio controls><source src="{}"></audio>'.format(mixture_path)
        self.content += '</td>'

        # a list of cells for audio and audio_sisdr
        for element in elements:
            key, val = element
            # fill a cell
            if key == 'text':
                self.content += '<td>'
                self.content += val
                self.content += '</td>'
            elif key == 'text_sisdr':
                self.content += '<td>'
                self.content += '<center>'
                self.content += 'Si-SDR={:.2f}'.format(val)
                self.content += '</center>'
            elif key == 'estimate_audio':
                self.content += '<audio controls><source src="{}"></audio>'.format(val)
                self.content += '</td>'
            elif key == 'change_row':
                self.content += '</tr><tr>'
            elif key == 'image':
                self.content += '<td>'
                self.content += '<img src="{}" style="max-height:256px;max-width:256px;">'.format(val)
                self.content += '</td>'
            elif key == 'audio':
                self.content += '<td>'
                self.content += '<audio controls><source src="{}"></audio>'.format(val)
                self.content += '</td>'
            elif key == 'video':
                self.content += '<td>'
                self.content += '<video src="{}" controls="controls" style="max-height:256px;max-width:256px;">'.format(val)
                self.content += '</td>'

        self.content += '</tr>'

    def write_html(self):
        self.content += '</body>' # Close body tag
        self.content += '</html>' # Close HTML tag
        with open(self.fn_html, 'w') as f:
            f.write(self.content)

if __name__ == '__main__':
    to_html("vis_dir", "index", sort_key={'ClosedSet':"avatasnet", "OpenSet":None})
