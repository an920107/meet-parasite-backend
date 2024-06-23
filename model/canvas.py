from enum import Enum

from pydantic import BaseModel


class Canvas(BaseModel):
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    canvas_width: float
    canvas_height: float
    stroke_style: str
    line_width: int
    line_cap: str
    line_dash: list[int]
    global_composite_operation: str
    font_type: str
    font_size: int
    text_max_width: int
    text_baseline: str
    content_text: str | None = None


class CanvasType(str, Enum):
    CIRCLE = "circle"
    TEXT = "text"
    RECTANGLE = "rectangle"
    LINE = "line"
