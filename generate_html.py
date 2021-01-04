import os
import glob
import json
import random
import matplotlib.pyplot as plt
import numpy as np

def to_html(root, html_name, sort_key):
    '''
    Args:
        root (str): Directory with all the files with following directory structure:
            vis_dir/
            ├── ClosedSet
            │   ├── avatasnet
            │   │   ├── final_metrics.json
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
            │   ├── avadptnet
            │   │   ├── final_metrics.json
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
    intro_visualizer = HTMLVisualizer(root, html_name, 'intro_page')

    # Check OpenSet and ClosedSet
    sets_present = []
    for folder in os.listdir(root):
        if folder=="OpenSet" and len(os.listdir(root+"/OpenSet"))>0:
            sets_present.append("OpenSet")
        elif folder=="ClosedSet" and len(os.listdir(root+"/ClosedSet"))>0:
            sets_present.append("ClosedSet")

    # Add page links
    intro_visualizer.add_sets(sets_present)
    intro_visualizer.write_html()

    # # Loop over sets
    for set_ in sets_present:
        set_dir = root+"/"+set_
        set_visualizer = HTMLVisualizer(set_dir, set_, 'set_page')
        models_present_files = os.listdir(set_dir) # Check Models present
        models_present = []
        # Remove html files
        for models_present_file in models_present_files:
            if '.' not in models_present_file:
                models_present.append(models_present_file)
        if len(models_present)>0:
            # Create table for Model Comparison
            set_visualizer.add_table("Model Comparison")
            header = ['Model', 'Si-SDR']
            set_visualizer.add_header(header)
            vis_rows = []
            sisdrs = []
            for model in models_present:
                with open(f'{set_dir}/{model}/final_metrics.json') as fp:
                    metrics = json.load(fp)
                    sisdr = metrics['si_sdr']
                    fp.close()
                sisdrs.append(sisdr)
                vis_rows.append([('model_link', model),('text', sisdr)])
            vis_rows = [x for _,x in sorted(zip(sisdrs, vis_rows), reverse=True)]
            set_visualizer.add_rows(vis_rows)
            set_visualizer.close_table()

            # Comparison Table
            # Audio examples
            set_visualizer.add_table(set_)
            # init headers
            header = ['Filename', 'Mixture Audio', 'Ground Truth']

            # Check number of sources
            model0_files_present = os.listdir(set_dir+"/"+models_present[0])
            # Keep only folders, remove files with extentions i.e. containing '.'
            model0_files = []
            for models0_file_present in model0_files_present:
                if '.' not in models0_file_present:
                    model0_files.append(models0_file_present)
            model0_ex0_path = set_dir+"/"+models_present[0]+"/"+model0_files[0]
            num_sources = len(glob.glob(model0_ex0_path+"/s*_estimate.wav"))

            for model in models_present:
                header.append(model)
            set_visualizer.add_header(header)

            # init rows
            vis_rows = []
            # get examples which are common among models
            dirs = None
            for model in models_present:
                if dirs is None:
                    dirs = set(map(lambda x: x.split('/')[-1], glob.glob(f'{root}/{set_}/{model}/ex_*')))
                else:
                    dirs = dirs.intersection(set(map(lambda x: x.split('/')[-1], glob.glob(f'{root}/{set_}/{model}/ex_*'))))
            dirs = list(dirs)
            example_nums = [ex.split('/')[-1] for ex in dirs]

            # Add rows
            vis_rows = []
            # set number of files to be chosen randomly
            # apart from worst 5 and best 5
            num_ex_compare = 5
            assert len(example_nums)>=10, f"For set {set_}, Number of examples to be \
                visualized should be in range [10, 10 + number of common examples among \
                models, which is {len(example_nums)}]"
            for ex in example_nums:
                row_elements = [('num_sources', num_sources), ('num_models', len(models_present))]
                # get mixture from first model
                with open(f'{root}/{set_}/{models_present[0]}/{ex}/metrics.json', 'r') as fp:
                    metrics = json.load(fp)
                    mixture_name = metrics['mix_path'].split('/')[-1].replace('.wav', '').replace('_', ' v.s. ')
                    fp.close()
                row_elements.append( ('mixture_name', mixture_name) )
                # get mixture audio from first model
                row_elements.append( ('mixture_path', f'{models_present[0]}/{ex}/mixture.wav') )

                for i in range(num_sources):
                    # get ground truth from first model
                    if i>0:
                        row_elements.append( ('change_row', None) )
                    row_elements.append( ('audio', f'{models_present[0]}/{ex}/s{i}.wav') )
                    for model in models_present:
                        with open(f'{root}/{set_}/{model}/{ex}/metrics.json', 'r') as fp:
                            metrics = json.load(fp)
                            row_elements.append( ('text_sisdr', metrics['si_sdr']) )
                            fp.close()
                        row_elements.append( ('estimate_audio', f'{model}/{ex}/s{i}_estimate.wav') )

                vis_rows.append(row_elements)

            # Sorting
            set_sort_key = sort_key[set_]
            sort_dirs = [f'{root}/{set_}/{set_sort_key}/{ex}' for ex in example_nums]
            # sort_dirs = glob.glob(f'{root}/{set_}/{set_sort_key}/ex_*')
            sisdrs = []
            for dd in sort_dirs:
                with open(f'{dd}/metrics.json', 'r') as fp:
                    metrics = json.load(fp)
                    sisdrs.append(metrics['si_sdr'])
                    fp.close()
            # sort by si_sdr
            vis_rows = [x for _,x in sorted(zip(sisdrs, vis_rows), reverse=True)] # Descending order
            final_vis_rows = vis_rows
            bottom_5 = vis_rows[-5:]
            top_5 = vis_rows[:5]
            max_random_len = len(example_nums[5:-5])
            if max_random_len>=num_ex_compare:
                random_n_idx = random.sample(range(len(example_nums[5:-5])), k=num_ex_compare)
            else:
                random_n_idx = random.sample(range(len(example_nums[5:-5])), k=max_random_len)
            random_n_idx.sort()
            final_vis_rows = []
            for i in top_5:
                final_vis_rows.append(i)
            for i in random_n_idx:
                final_vis_rows.append(vis_rows[5+i])
            for i in bottom_5:
                final_vis_rows.append(i)

            # write set HTML file
            set_visualizer.add_rows(final_vis_rows)
            set_visualizer.close_table()
            set_visualizer.write_html()

            # Model Page
            for model in models_present:
                model_dir = set_dir+"/"+model
                model_visualizer = HTMLVisualizer(model_dir, model, 'model_page')
                # Create Model histogram
                dirs = glob.glob(f'{model_dir}/ex_*/')
                sisdrs = []
                for dd in dirs:
                    with open(f'{dd}metrics.json', 'r') as fp:
                        metrics = json.load(fp)
                        sisdrs.append(metrics['si_sdr'])
                        fp.close()
                plt.hist(sisdrs, bins=int(np.sqrt(len(sisdrs)))) # TODO: check number of bins
                plt.xlabel('Mean = {:.4f}, Median = {:.4f}'.format(np.mean(sisdrs), np.median(sisdrs)))
                plt.title('Histogram for {}'.format(model))
                plt.savefig(f'{model_dir}/histogram.png')
                plt.clf()
                model_visualizer.add_image('histogram.png')

                # Examples table
                model_visualizer.add_table(model)
                header = ['Filename', 'Mixture Audio', 'Ground Truth', model]
                model_visualizer.add_header(header)
                vis_rows = []
                example_dirs = glob.glob(f'{root}/{set_}/{model}/ex_*')

                # Loop over examples
                for ex_dir in example_dirs:
                    row_elements = [('num_sources', num_sources), ('num_models', len(models_present))]
                    # get mixture from model
                    with open(f'{ex_dir}/metrics.json', 'r') as fp:
                        metrics = json.load(fp)
                        mixture_name = metrics['mix_path'].split('/')[-1].replace('.wav', '').replace('_', ' v.s. ')
                        fp.close()
                    row_elements.append( ('mixture_name', mixture_name) )
                    # get mixture audio from model
                    row_elements.append( ('mixture_path', f'{ex_dir.split("/")[-1]}/mixture.wav') )

                    for i in range(num_sources):
                        # get ground truth from model
                        if i>0:
                            row_elements.append( ('change_row', None) )
                        row_elements.append( ('audio', f'{ex_dir.split("/")[-1]}/s{i}.wav') )
                        with open(f'{ex_dir}/metrics.json', 'r') as fp:
                            metrics = json.load(fp)
                            row_elements.append( ('text_sisdr', metrics['si_sdr']) )
                            fp.close()
                        row_elements.append( ('estimate_audio', f'{ex_dir.split("/")[-1]}/s{i}_estimate.wav') )
                    
                    vis_rows.append(row_elements)
                
                # Sorting
                sort_dirs = example_dirs
                sisdrs = []
                for dd in sort_dirs:
                    with open(f'{dd}/metrics.json', 'r') as fp:
                        metrics = json.load(fp)
                        sisdrs.append(metrics['si_sdr'])
                        fp.close()
                # sort by si_sdr
                vis_rows = [x for _,x in sorted(zip(sisdrs, vis_rows), reverse=True)] # Descending order

                model_visualizer.add_rows(vis_rows)
                model_visualizer.close_table()
                model_visualizer.write_html()


class HTMLVisualizer():
    def __init__(self, save_path, fn_html, page_type):
        '''
        Args:
            save_path: (string): save path
            fn_html: (string): name of HTML file without .html
            page_type: (string): Type of page out of 'intro_page',
                'set_page', 'model_page'.
                'set_page'-> 'OpenSet' or 'ClosedSet'
                'model_page'-> model folder names
        '''
        self.save_path = save_path
        self.fn_html = fn_html
        self.page_type = page_type
        self.content = '<!DOCTYPE html> <html>' # Add HTML tag
        if page_type=='intro_page':
            self.content += '<head><meta charset="utf-8"> \
                <title>Audio Source Separation</title></head>' # Add title
            self.content += '<body>' # Add body tag
            self.content += '<center><h1>Audio Source Separation</h1></center>' # Add heading
        else:
            self.content += f'<head><meta charset="utf-8"> \
                <title>{fn_html}</title></head>' # Add title
            self.content += '<body>' # Add body tag
            self.content += f'<center><h1>{fn_html}</h1></center>' # Add heading

    def add_sets(self, sets_present):
        for set_ in sets_present:
            self.content += '<center><p><a href="{}/{}/{}.html">{}</a></p></center>'.format(self.save_path, set_, set_, set_)

    def add_table(self, table_name):
        self.content += '<center><h2>{}</h2></center>'.format(table_name)
        self.content += '<center>'
        self.content += '<table>'
        self.content += '<style> table, \
        th, \
        td {border: 1px solid black;}, \
        table {width: 100% !important;}, \
        audio {width: 220px; display: block;}, \
        </style>'

    def close_table(self):
        self.content += '</table>'
        self.content += '</center>'

    def add_header(self, elements):
        self.content += '<tr>'
        for element in elements:
            self.content += '<th>{}</th>'.format(element)
        self.content += '</tr>'
    
    def add_image(self, img_name):
        '''
        Args:
            img_name (string): Image name with extension
        '''
        img_dim_px = 120 # Image dimension in pixels (4:3 ratio, width:height)
        self.content += '<center>'
        self.content += '<img src="{}" alt="{}" \
            style="width:{}px;height:{}px;">'.format(img_name, \
                img_name.split('.')[0], img_dim_px*4, img_dim_px*3)
        self.content += '</center>'

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def add_row(self, elements):
        self.content += '<tr>'

        # get important variables
        mixture_name = num_sources = num_models = mixture_path = None
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
        if mixture_name is not None:
            self.content += '<td rowspan="{}">'.format(num_sources)
            self.content += mixture_name
            self.content += '</td>'

        # add mixture audio
        if mixture_path is not None:
            self.content += '<td rowspan="{}">'.format(num_sources)
            self.content += '<audio controls class="audio-player" preload="metadata"> \
                <source src="{}" type="audio/wav"></audio>'.format(mixture_path)
            self.content += '</td>'

        # a list of cells for audio and audio_sisdr
        for element in elements:
            key, val = element
            # fill a cell
            if key == 'text':
                self.content += '<td>'
                if isinstance(val, float):
                    self.content += '{:.4f}'.format(val)
                else:
                    self.content += str(val)
                self.content += '</td>'
            elif key == 'model_link':
                self.content += '<td>'
                self.content += '<a href="{}/{}.html">{}</a>'.format(val, val, val)
                self.content += '</td>'
            elif key == 'text_sisdr':
                self.content += '<td>'
                self.content += '<center>'
                self.content += 'Si-SDR={:.2f}'.format(val)
                self.content += '</center>'
            elif key == 'estimate_audio':
                self.content += '<audio controls class="audio-player" preload="metadata"> \
                    <source src="{}" type="audio/wav"></audio>'.format(val)
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
        # Check folders
        if self.page_type=='intro_page':
            html_file_path = f'{self.fn_html}.html'
        else:
            html_file_path = f'{self.save_path}/{self.fn_html}.html'
        with open(html_file_path, 'w') as f:
            f.write(self.content)
        print(f'Saved HTML file {html_file_path}')

if __name__ == '__main__':
    to_html("vis_dir", "index", sort_key={'ClosedSet':"avatasnet", "OpenSet":"AvaDPTNet"})
