#PINK = H: 153.0       S: 192.0        V: 93.0
#BLUE ON WHITE = H: 105.0       S: 240.0        V: 154.0
#BLACK ON WHITE = 13, 80, 60
#GREEN ON WHITE = 85, 230, 160

import cv
import cv2
import numpy as np


def track_color(img, color):
    # Green settings
    GREEN_MIN = np.array([42, 186, 99], np.uint8)
    GREEN_MAX = np.array([100, 255, 255], np.uint8)

    # Pink settings
    PINK_MIN = np.array([140, 50, 99], np.uint8)
    PINK_MAX = np.array([180, 255, 255], np.uint8)

    if color == 'green':
        color_min = GREEN_MIN
        color_max = GREEN_MAX
    elif color == 'pink':
        color_min = PINK_MIN
        color_max = PINK_MAX
    else:
        raise Exception('Invalid color parameter')

#    img = cv2.imread('cam_home.jpeg')

    cv.Smooth(cv.fromarray(img), cv.fromarray(img), cv.CV_BLUR, 3);
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    frame_threshed = cv2.inRange(hsv_img, color_min, color_max)

#    cv2.imwrite('output_thresholded.jpeg', frame_threshed)
    contours, hierarchy = cv2.findContours(frame_threshed,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    coord_list = []
    for cnt in contours:
	 area = cv2.contourArea(cnt)
	 if area>500:
	 	M = cv2.moments(cnt)
	        centroid_x = int(M['m10']/M['m00'])
	        centroid_y = int(M['m01']/M['m00'])
	        coord_list.append((centroid_x,centroid_y))

    cv2.drawContours(img, contours, -1, (0, 255, 0), 5)

    return coord_list, img

if __name__ == '__main__':
    track_color('green')
    #track_color('pink')

