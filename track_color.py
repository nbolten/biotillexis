#OpenCV
import cv
import cv2

#Built-in Library
import numpy as np


#Function: Takes in an image and color parameter.
#Returns list of coordinates of objects of that color in the image.
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

    #Filter out image noise
    cv.Smooth(cv.fromarray(img), cv.fromarray(img), cv.CV_BLUR, 3)
    #Convert image to hsv
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    #Check for colors withing range of input color
    frame_threshed = cv2.inRange(hsv_img, color_min, color_max)
    #Form contours around elements of chosen color
    contours, hierarchy = cv2.findContours(frame_threshed,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    coord_list = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        #Discard contours of elements that are too small
        if area > 500:
            M = cv2.moments(cnt)
            centroid_x = int(M['m10']/M['m00'])
            centroid_y = int(M['m01']/M['m00'])
            coord_list.append((centroid_x, centroid_y))
    #Draw final contours on image
    cv2.drawContours(img, contours, -1, (0, 255, 0), 5)
    #Return contour coordinates and final image
    return coord_list, img

if __name__ == '__main__':
    track_color('green')
    #track_color('pink')
