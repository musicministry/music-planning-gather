from great_tables import GT, loc, style, from_column
from IPython.display import display, Markdown
from titlecase import titlecase
import pandas as pd
import requests
import yaml
import re

# =============================================================================
# Load video YAMLs from GitHub

# Gather index
gather_index_url = 'https://raw.githubusercontent.com/musicministry/song-urls/refs/heads/gather/gather.yml'
gather_index = yaml.safe_load(requests.get(gather_index_url).content)

# Anthem index
supplemental_index_url = 'https://raw.githubusercontent.com/musicministry/song-urls/refs/heads/supplemental/supplemental.yml'
anthem_index = yaml.safe_load(requests.get(supplemental_index_url).content)

# Mass settings index
mass_index_url = 'https://raw.githubusercontent.com/musicministry/song-urls/refs/heads/gather/mass-settings.yml'
mass_index = yaml.safe_load(requests.get(mass_index_url).content)

# Combine to support URL lookup
gather_index = gather_index | anthem_index | mass_index

# -----------------------------------------------------------------------------

def keyify(string: str):
    """Convert human-readable titlecase to lowercase hyphen-separated string."""
    # Remove notes, if any
    if "|" in string:
        string = string.split("(")[0].strip()
    # Remove punctuation and special characters
    string = re.sub(r'[^a-zA-Z0-9]', ' ', string).strip().lower()
    return '-'.join(string.split())

def get_hymn_url(hymn):
    """Get video URL for 'hymn' from `urls`. Returns 'No URL found' if the hymn is not found in the URL list."""
    # Append composer name, if available, to hymn name
    hymn_key = hymn['name'] + f' ({hymn["composer"]}' if 'composer' in hymn.keys() else hymn['name']
    # Append hymn tune, if available
    hymn_key = hymn_key + f' ({hymn["tune"]})' if 'tune' in hymn.keys() else hymn_key
    # Remove punctuation and special characters
    hymn_key = re.sub('[^A-Za-z0-9 ]+', '', hymn_key.strip())
    # Replace spaces and make lowercase
    hymn_key = hymn_key.replace('  ', ' ').replace(' ', '-').lower()
    # Add hyperlink
    if keyify(hymn_key) in gather_index.keys():
        return gather_index[keyify(hymn_key)]['url']
    else:
        return None

def get_url(name, swap=False):
    """Return the video URL for hymn or song `name`. If the `name` has a colon and needs to be swapped, for example, `Gloria: Heritage Mass` needs to become `Heritage Mass: Gloria`, use `swap = True`."""
    # Reverse the name, if needed
    if swap:
        name = ' '.join(name.split(': ')[::-1])

    # Extract the URL
    if keyify(name) in gather_index.keys():
        return gather_index[keyify(name)]['url']
    else:
        return None

def to_small_caps(text):
    small_caps = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ',
        'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ',
        'p': 'ᴘ', 'q': 'Q', 'r': 'ʀ', 's': 's', 't': 'ᴛ',
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ',
        'z': 'ᴢ'
    }
    return ''.join(small_caps.get(char, char) for char in text.lower())

def make_name(hymn, index=None):
    """Append hymn tune, composer, and/or verses to title and add hyperlink to video."""
    new_text = titlecase(hymn['name']) + f' (<span style="font-variant:small-caps;">{hymn["tune"].lower()}</span>)' if 'tune' in hymn.keys() else titlecase(hymn['name'])
    # Add URL, if available
    hymn_url = get_hymn_url(hymn=hymn)
    if hymn_url is not None:
        if index is not None:
            new_text = f'[{new_text}]({hymn_url})\\index[{index}]{{new_text}}'
        else:
            new_text = f'[{new_text}]({hymn_url})'
    # Add year, if available
    new_text = f'<b>Year {hymn["year"]}:</b> ' + new_text if 'year' in hymn.keys() else new_text
    # Add composer name, if available
    new_text = new_text + f' ({hymn["composer"].title()})' if 'composer' in hymn.keys() else new_text
    # Add verses, if available
    new_text = new_text + f' (<i>verses {hymn["verses"]}</i>)' if 'verses' in hymn.keys() else new_text
    # Add note, if available
    new_text = new_text + f' ({hymn["note"]})' if 'note' in hymn.keys() else new_text
    return new_text

def make_psalm(psalm, index=None):
    """Append tune, composer, and/or verses to title and add hyperlink to video."""
    new_text = psalm['name'] + f' (<span style="font-variant:small-caps;">{psalm["tune"]}</span>)' if 'tune' in psalm.keys() else psalm['name']
    # Add URL, if available
    psalm_url = get_hymn_url(hymn=psalm)
    if psalm_url is not None:
        if index is not None:
            new_text = f'[{new_text}]({psalm_url})\\index[{index}]{{new_text}}'
        else:
            new_text = f'[{new_text}]({psalm_url})'
    # Add composer name, if available
    new_text = new_text + f' ({psalm["composer"].title()})' if 'composer' in psalm.keys() else new_text
    # Add verses, if available
    new_text = new_text + f' (<i>verses {psalm["verses"]}</i>)' if 'verses' in psalm.keys() else new_text
    # Add note, if available
    new_text = new_text + f' ({psalm["note"]})' if 'note' in psalm.keys() else new_text
    return new_text

def hymnlist(hymns, index=None):
    """Create a hymn list table from contents of `hymns`"""
        
    def remove_dupes(l, char=''):
        """Replace duplicated items in list `l` with `char`"""
        tmp = list()
        for i in l:
            if i in tmp:
                tmp.append(char)
            else:
                tmp.append(i)
        return tmp
    
    # Remove unused keys
    hymnsnew = hymns.copy()
    hymnsnew.pop('anthems', None)

    # Create a dataframe
    df = pd.DataFrame({
        'hymn': remove_dupes([titlecase(hymn.replace('-', ' ')) for hymn in hymnsnew for i in hymns[hymn]['list']]),
        'hymnal': [(i['book'] if '](' in i['book'].lower() else ''.join(l for l in i['book'] if l.isupper())) if 'book' in i.keys() else '' for hymn in hymnsnew for i in hymns[hymn]['list']],
        'options': [f'<i>{make_psalm(i, index=index)}</i>' if 'psalm' in hymn else make_name(i, index=index) for hymn in hymnsnew for i in hymns[hymn]['list']],
        'priority': [i['priority'] if 'priority' in i.keys() else 'none' for hymn in hymnsnew for i in hymns[hymn]['list']]
    })
    df['options'] = df['options'].str.replace('Verses', 'verses')

    # Preference coloring
    red = '#bd3732;'
    color_map = {
        'none': '#FFFFFF',      # White
        'required': '#f5b7b1',  # Semi-transparent red
        'preferred': '#fad7a0', # Semi-transparent orange
        'optional': '#f9e79f',  # Semi-transparent yellow
        'flexible': '#a9dfbf'   # Semi-transparent green
    }
    df = df.assign(
        background=(df['priority'].replace(color_map))
    )

    # Create and format HTML table
    gtbl = GT(df, rowname_col='hymn')
    gtbl = (gtbl
            .tab_style(locations=loc.stub(),
                       style=style.text(align='right', v_align='top', weight='bold'))
            .tab_style(locations=loc.body(columns='hymnal'),
                       style=[style.fill(color=from_column(column='background')), style.text(v_align='top')])
            .cols_hide(columns=['priority', 'background'])
            .cols_align(columns='hymnal', align='center')
            .cols_width(cases={'hymnal': '10%', 'options': '80%'})
            .tab_options(table_width='100%', column_labels_hidden=True,
                         table_body_hlines_width='0pt',
                         row_striping_background_color=None)
            .fmt_markdown(columns=['hymnal', 'options'])
            )
    gtbl.show()

def masssetting(mass, index=None):
    """Create a Mass setting table from contents of `mass` and URLs from 'urls'"""
        
    def remove_dupes(l, char=''):
        """Replace duplicated items in list `l` with `char`"""
        tmp = list()
        for i in l:
            if i in tmp:
                tmp.append(char)
            else:
                tmp.append(i)
        return tmp
    
    def make_part(hymn, part, index=None):
        """Append hymn tune, composer, and/or verses to title and add hyperlink to video."""
        # Get URL
        if part.lower() == 'holy-holy-holy':
            part = 'holy'
        hymn_key = titlecase(f'{hymn["name"]}: {part}')
        if 'option' in hymn.keys():
            hymn_key = f'{hymn_key} {hymn["option"][0]}'
        hymn_url = get_url(name=hymn_key)

        # Add URL
        new_text = titlecase(hymn['name'])
        if hymn_url is not None:
            if index is not None:
                new_text = f'[{new_text}]({hymn_url})\\index[{index}]{{new_text}}'
            else:
                new_text = f'[{new_text}]({hymn_url})'
        # Add year, if available
        new_text = f'<b>Year {hymn["year"]}:</b> ' + new_text if 'year' in hymn.keys() else new_text
        # Add option, if available
        new_text = new_text + f', {hymn["option"]}' if 'option' in hymn.keys() else new_text
        # Add tune, if available
        new_text = new_text + f' (Tune: {hymn["tune"]})' if 'tune' in hymn.keys() else new_text
        # Add composer name, if available
        new_text = new_text + f' ({hymn["composer"].title()})' if 'composer' in hymn.keys() else new_text
        # Add note, if available
        new_text = new_text + f' ({hymn["note"]})' if 'note' in hymn.keys() else new_text
        return new_text
    
    # Create a dataframe
    df = pd.DataFrame({
        'hymn': remove_dupes([titlecase(part.replace('-', ' ')) for part in mass for i in mass[part]['list']]),
        'hymnal': [(i['book'] if '](' in i['book'].lower() else ''.join(l for l in i['book'] if l.isupper())) if 'book' in i.keys() else '' for part in mass for i in mass[part]['list']],
        'options': [make_part(i, part=part, index=index) for part in mass for i in mass[part]['list']],
        'priority': [i['priority'] if 'priority' in i.keys() else 'none' for part in mass for i in mass[part]['list']]
    })
    df['options'] = df['options'].str.replace('Verses', 'verses')
    df['hymn'] = df['hymn'].str.replace("Holy Holy Holy", "Holy, Holy, Holy")
    df['options'] = df['options'].str.replace('During', 'during')
    
    # Preference coloring
    red = '#bd3732;'
    color_map = {
        'none': '#FFFFFF',      # White
        'required': '#f5b7b1',  # Semi-transparent red
        'preferred': '#fad7a0', # Semi-transparent orange
        'optional': '#f9e79f',  # Semi-transparent yellow
        'flexible': '#a9dfbf'   # Semi-transparent green
    }
    df = df.assign(
        background=(df['priority'].replace(color_map))
    )

    # Create and format HTML table
    gtbl = GT(df, rowname_col='hymn')
    gtbl = (gtbl
            .tab_style(locations=loc.stub(),
                       style=style.text(align='right', v_align='top', weight='bold'))
            .tab_style(locations=loc.body(columns='hymnal'),
                       style=[style.fill(color=from_column(column='background')), style.text(v_align='top')])
            .cols_hide(columns=['priority', 'background'])
            .cols_align(columns='hymnal', align='center')
            .cols_width(cases={'hymnal': '10%', 'options': '75%'})
            .tab_options(table_width='100%', column_labels_hidden=True,
                         table_body_hlines_width='0pt',
                         row_striping_background_color=None)
            .fmt_markdown(columns=['hymnal', 'options'])
            )
    gtbl.show()


def check_parts(yml):
    """Check Mass parts in `yml` for expected values. Accepted options are:
      'processional', 'opening', 'offertory', 'preparation',
      'preparation-of-gifts', 'psalm', 'responsorial-psalm',
      'gospel-acclamation', 'communion', 'meditation', 'second-communion',
      'recessional', 'closing', 'anthems',
      'ashes', 'distribution-of-ashes',
      'washing-of-feet', 'transfer-of-the-blessed-sacrament',
      'veneration-of-the-cross', 'psalm-after-first-reading',
      'psalm-after-second-reading', 'psalm-after-third-reading',
      'psalm-after-fourth-reading', 'psalm-after-fifth-reading',
      'psalm-after-sixth-reading', 'psalm-after-seventh-reading',
      'psalm-after-epistle', 'litany-of-the-saints', 'after-each-baptism',
      'sprinking-rite', 'sprinkling', 'marian-antiphon', 'sequence',
      'kyrie', 'gloria', 'holy-holy-holy', 'memorial-acclamation', 'amen', 'lamb-of-god
    
    Arguments
    ---------
        yml (str): YAML block from front matter to inspect
    
    Raises
    ------
        NameError if a Mass part in `yml` is not an expected entry.
    """

    # Acceptable values
    options = set([
      'processional', 'opening', 'offertory', 'preparation', 'preparation-of-gifts', 'psalm', 'responsorial-psalm', 'gospel-acclamation', 'communion', 'meditation', 'second-communion', 'recessional', 'closing', 'anthems',
      'ashes', 'distribution-of-ashes', 'washing-of-feet', 'transfer-of-the-blessed-sacrament', 'veneration-of-the-cross',
      'psalm-after-first-reading', 'psalm-after-second-reading', 'psalm-after-third-reading', 'psalm-after-fourth-reading', 'psalm-after-fifth-reading', 'psalm-after-sixth-reading', 'psalm-after-seventh-reading', 'psalm-after-epistle', 'litany-of-the-saints', 'after-each-baptism', 'sprinking-rite', 'marian-antiphon', 'sprinkling', 'sequence',
      'kyrie', 'gloria', 'holy-holy-holy', 'memorial-acclamation', 'amen', 'lamb-of-god'])

    def flatten(xss):
        return [x for xs in xss for x in xs]

    # Get the first key (could be 'hymns', 'mass', or something else)
    head = yml[list(yml.keys())[0]]

    hymn_name_errors = set(flatten([list(head[i].keys()) for i in head.keys()])).difference(options)
        
    if len(hymn_name_errors) > 0:
        raise NameError(f'`{", ".join(hymn_name_errors)}` is/are not recognized. See `?check_parts` for accepted Mass parts. Please check spelling and try again.')    
    
def check_priorities(yml):
    """Check priorities for expected values. Accepted options are:
      'required', 'preferred', 'optional', 'flexible'
    
    Arguments
    ---------
        yml (str): YAML block from front matter to inspect
    
    Raises
    ------
        NameError if a Mass part in `yaml` is not an expected entry.
    """

    # Acceptable values    
    priorities = set(['none', 'required', 'preferred', 'optional', 'flexible'])
    
    # Get the first key (could be 'hymns', 'mass', or something else)
    head = yml[list(yml.keys())[0]]
    
    # Perform check
    passed = [head[y][hymn]['list'][l]['priority'] if 'priority' in head[y][hymn]['list'][l].keys() else 'none' for y in head.keys() for hymn in head[y].keys() for l in range(len(head[y][hymn]['list'])) if hymn not in ['anthems']]
    priority_errors = set(passed).difference(priorities)
    
    if len(priority_errors) > 0:
        raise NameError(f'`{", ".join(priority_errors)}` is/are not recognized. See `?check_priorities` for accepted entries. Please check spelling and try again.')

def get_params(yml):
    """Load front matter YAML as passed to `yml` and check for errors.
    
    Arguments
    ---------
        yml (str): YAML block from front matter to load and inspect

    Returns
    -------
        dict: YAML from `yml` parsed as dictionary
    """
    params = yaml.safe_load(yml)
    check_parts(params)
    check_priorities(params)
    return params

def check_for_anthems(params):
    for ls in params.values():
        if 'anthems' in ls.keys():
            return True
        else:
            pass
    return False

def anthemlist(hymns, index=None):
    """Create a table of choral anthem suggestions as listed in `hymns` with video URLs"""
    
    if check_for_anthems(hymns):
    
        display(Markdown('::: {.red}\n'))
        display(Markdown('### Choral Anthems\n'))
        display(Markdown(':::'))
        
        display(Markdown('|          |                                  |'))
        display(Markdown('|:--------:|:---------------------------------|'))
        for yr, ls in hymns.items():
            if 'anthems' in ls.keys():
                if yr == 'abc':
                    display(Markdown('| [**Years A, B, C**]{.red} | %s |' % ("\n | |".join([make_name(i, index=index) for i in ls["anthems"]["list"] if "anthems"]))))                    
                else:
                    display(Markdown('| [**Year %s**]{.red} | %s |' % (yr.upper(), "\n | |".join([make_name(i, index=index) for i in ls["anthems"]["list"] if "anthems"]))))
        display(Markdown(': Choral anthems could be sung before Mass, in place of an offertory hymn, in place of a Communion hymn (if appropriate), or after Communion for meditation. {tbl-colwidths="[15,85]"}'))
