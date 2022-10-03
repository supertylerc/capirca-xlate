from _typeshed import Incomplete
from pathlib import Path
from ruamel.yaml.compat import StreamTextType
from typing import Any, Optional, Text, Union

class YAML:
    typ: Incomplete
    pure: Incomplete
    plug_ins: Incomplete
    Resolver: Incomplete
    allow_unicode: bool
    Reader: Incomplete
    Representer: Incomplete
    Constructor: Incomplete
    Scanner: Incomplete
    Serializer: Incomplete
    default_flow_style: Incomplete
    comment_handling: Incomplete
    Emitter: Incomplete
    Parser: Incomplete
    Composer: Incomplete
    stream: Incomplete
    canonical: Incomplete
    old_indent: Incomplete
    width: Incomplete
    line_break: Incomplete
    map_indent: Incomplete
    sequence_indent: Incomplete
    sequence_dash_offset: int
    compact_seq_seq: Incomplete
    compact_seq_map: Incomplete
    sort_base_mapping_type_on_output: Incomplete
    top_level_colon_align: Incomplete
    prefix_colon: Incomplete
    version: Incomplete
    preserve_quotes: Incomplete
    allow_duplicate_keys: bool
    encoding: str
    explicit_start: Incomplete
    explicit_end: Incomplete
    tags: Incomplete
    default_style: Incomplete
    top_level_block_style_scalar_no_indent_error_1_1: bool
    scalar_after_indicator: Incomplete
    brace_single_entry_mapping_in_flow_sequence: bool
    def __init__(
        self,
        *,
        typ: Optional[Text] = ...,
        pure: Any = ...,
        output: Any = ...,
        plug_ins: Any = ...
    ) -> None: ...
    def load(self, stream: Union[Path, StreamTextType]) -> dict[str, Any]: ...
