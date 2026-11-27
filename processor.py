
import cv2

"""Модуль обработки видео"""



def process_frame(frame):

    height, width = frame.shape[:2]

    cv2.rectangle(
        frame,
        (width // 4, height // 4),
        (width * 3 // 4, height * 3 // 4),
        (0, 255, 0),
        3
    )

    cv2.putText(
        frame,
        "Processed by Python",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    return frame
