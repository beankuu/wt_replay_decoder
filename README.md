# Warthunder Replay Decoder

Thanks to

- Yay5379/wt_client_replay_parser
- nilshellerhoff/warthunder-replay-parser
- klensy/wt-tools
- kotiq/wt-tools

## Description

Decoding Warthunder Replay

Focusing on rest_of_file part rather than header/m_set

Supports Server Replays only for now, but same logic applies to client replay

### 1replay_list

Get List of replays from Gaijin server to json file

Not so much functionality for now

### 2download_replay

currently exact copy of nilshellerhoff/warthunder-replay-parser/download_replay.py

### 3wrpl2decode

args : 1 server replay directory

Output1 : Decoded Raw Hex Strings, split by each block
Output2 : Filtered out information

Core Struct structure from Yay5379/wt_client_replay_parser and wt-tools

## TODO

1. combine 1replay_list and 2download_replay
2. Better #Filtering(pass2)
