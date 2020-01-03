"""Generates assets for web display of Android font info."""
import android_fonts
import copy
import emoji
import json
import os

def _out(file):
  return os.path.join(os.path.expanduser('~/oss/rsheeter.github.io/android_fonts'),
                      file)

_SUMMARY = _out('emoji_summary.json')
_EMOJI = _out('emoji_detail.json')

def _font_summary():
  df = android_fonts.metadata()
  sf = (df
        .groupby(['api_level'])
        .agg({'font_file': 'count', 'file_size': 'sum'}))
  sf['file_size'] = sf['file_size'].apply(lambda sz: (sz / pow(2, 20)))
  sf.rename(columns = {
    'font_file': 'num_files',
    'file_size': 'size_MB',
  }, inplace=True)

  sf['delta_size_MB'] = sf['size_MB'] - sf['size_MB'].shift(1)

  sf.reset_index(inplace=True)

  return sf

def _emoji_df():
  df = android_fonts.emoji_support()
  # merge emoji metadata to gain the status column
  df = df.merge(emoji.metadata().drop(columns=['emoji_level']),
                on='codepoints')

  df = df[df['status'] == 'fully-qualified']
  df = df.drop(columns='status')

  df.supported = df.supported.astype('int32')

  df['api_level'] = df.font_file.str.split('/').str[1]
  df.api_level = df.api_level.astype('int32')
  df['font_file'] = df.font_file.str.split('/').str[2]

  return df

def _emoji_summary():
  df = _emoji_df()

  sf = (df.groupby(['font_file', 'api_level', 'emoji_level'])
        .agg({'supported': ['sum', 'count']}))
  sf.columns = ['supported', 'total']
  sf.reset_index(inplace=True)

  sf2 = (sf.drop(columns='emoji_level')
        .groupby('api_level')
        .agg('sum')
        .reset_index())
  sf2['delta'] = sf2['supported'] - sf2['supported'].shift(1)
  sf2.fillna(0, inplace=True)

  return sf, sf2

def _add_font_info(summary):
  sf = _font_summary()
  for rec in json.loads(sf.to_json(orient='records')):
    api_level = rec['api_level']
    del rec['api_level']
    summary[api_level]['fonts'] = rec

def _add_emoji_info(summary):
  by_emoji_level, by_api_level = _emoji_summary()

  for rec in json.loads(by_emoji_level.to_json(orient='records')):
    api_level = rec['api_level']
    del rec['api_level']
    del rec['font_file']
    summary[api_level]['emoji']['by_level'].append(rec)

  for _, row in by_api_level.iterrows():
    emoji = summary[row.api_level]['emoji']
    emoji['delta'] = row.delta
    emoji['supported'] = row.supported

def _make_summary_json():
  # init summary with no font or emoji data
  summary = {}
  for api_level, (name, version) in android_fonts.api_levels().items():
    summary[api_level] = {
      'name': name,
      'version': version,
      'fonts': None,
      'emoji': {
        'delta': 0,
        'supported': 0,
        'by_level': []
      },
    }

  _add_font_info(summary)
  _add_emoji_info(summary)

  with open(_SUMMARY, 'w') as f:
    f.write(json.dumps(summary, indent=2))
  print(f'Wrote {_SUMMARY}')

def _make_emoji_json():
  # meant for searching emoji sequences
  df = _emoji_df()
  df['api_support'] = (df[['api_level', 'supported']]
                       .apply(lambda t: (t.api_level, t.supported), axis=1))

  df = (df.groupby(['codepoints', 'emoji_level'])
        .agg({
              'api_support': lambda t: {api for api, supported in t if supported},
              'notes': lambda n: n.unique(),
             }))
  df.reset_index(inplace=True)

  with open(_EMOJI, 'w') as f:
    f.write(json.dumps(json.loads(df.to_json(orient='records')), indent=2))
  print(f'Wrote {_EMOJI}')

def _save_graph(ax, filename):
  ax.get_figure().savefig(_out(filename))
  print(f'Wrote {_out(filename)}')

def _make_graphs():
  df = _font_summary()
  _save_graph(df.plot.bar(x='api_level', y='size_MB'),
              'size_total.png')
  _save_graph(df.plot.bar(x='api_level', y='delta_size_MB'),
              'size_change.png')

def main():
  _make_summary_json()
  _make_emoji_json()
  _make_graphs()

if __name__ == '__main__':
  main()
