import numpy as np
import cv2
import math
from copy import deepcopy

inputMode = False
frame = None
roiPts = []

# 320 60

def get_safe_width(angle):
    return -0.5 * angle + 55

def get_road_width(angle):
    return (-16.0/3.0) * angle + 480

def mycopy(array):
    li = []
    for i in array:
        li.append([int(i[0]), int(i[1])])
    return np.array(li)

# def click_and_crop(event, x, y, flags, param):
#     global frame, roiPts, inputMode
#
#     if inputMode and event == cv2.EVENT_LBUTTONDOWN and len(roiPts) < 4:
#         roiPts.append((x, y))
#         cv2.circle(frame, (x, y), 4, (0, 0, 255), 2)
#         cv2.imshow("image", frame)

 # cv2.namedWindow("image")
# cv2.setMouseCallback("image", click_and_crop)

cap = cv2.VideoCapture('misdrive.avi')
fgbg = cv2.createBackgroundSubtractorMOG2()
mid_height = cap.get(4)/2

i = 0
prev_x = 0
prev_y = 0
center_x = 0
center_y = 0
prev_deviation=0
deviation=0
cur_speed = 0
prev_speed = 0
lc = 0
rc = 0
cur_dist=0
t_dist = 0

cap_rate = 5

ret, frame = cap.read()

# while True:
#     cv2.imshow("image", frame)
#     key = cv2.waitKey(1) & 0xFF
#     if key == ord("i") and len(roiPts) < 4:
#         inputMode = True
#         orig = frame.copy()
#
#         while len(roiPts) < 4:
#             cv2.imshow("image", frame)
#             cv2.waitKey(0)
#         break

while True:

    ret, frame = cap.read()
    if not ret:
        break

    edges = cv2.Canny(frame, 100, 200)
    display = edges.copy()
    # display = cv2.cvtColor(display, cv2.COLOR_GRAY2BGR)


    # if i == 200:
    #     print len(edges)
    #     for x in edges:
    #         print x
    i += 1


    fgmask = fgbg.apply(frame)
    fgmask = cv2.erode(fgmask, None, iterations=2)
    fgmask = cv2.dilate(fgmask, None, iterations=2)
    left = np.zeros((606, 548), np.uint8)
    right = np.zeros((606, 548), np.uint8)

    if fgmask.any():

        cnts = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_NONE)[-2]
        if cnts:

            # x, y, w, h = cv2.boundingRect(c)
            # cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

            c = max(cnts, key=cv2.contourArea)

            # epsilon = 0.003 * cv2.arcLength(c, True)
            # approx = cv2.approxPolyDP(c, epsilon, True)
            # c = approx
            # print c, len(c)
            # cv2.drawContours(frame, c, -1, (128, 255, 0), 2)

            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = np.int0(box)

            cv2.drawContours(display, [box], 0, (255, 255, 0), -1)

            if i == 1:
                for xy in box:
                    center_x += xy[0]
                for xy in box:
                    center_y += xy[1]
                center_x/=4
                center_y/=4

                angle = (60.0 - (((center_y - mid_height) * 1.0) / mid_height * 60.0)) + 30.0
                cur_dist = 10 * math.tan(math.radians(angle))


            if i % cap_rate == 0:
                prev_speed = cur_speed
                prev_x = center_x
                prev_y = center_y
                center_x = 0
                center_y = 0
                prev_dist = cur_dist
                prev_angle = angle

                for xy in box:
                    center_x += xy[0]
                for xy in box:
                    center_y += xy[1]

                center_x/=4.0
                center_y/=4.0

                angle = (60.0 - (((center_y - mid_height) * 1.0)/mid_height * 60.0)) + 30.0
                # cur_speed = math.sqrt(pow(center_x - prev_x, 2) + pow(center_y - prev_y, 2))
                cur_speed = math.sqrt(pow(center_x - prev_x, 2) + pow(center_y - prev_y, 2))
                # prev_deviation = deviation
                # deviation = (center_x - prev_x) * (100 - get_safe_width(angle)) * 0.01
                # print ((deviation - prev_deviation)/prev_deviation) * 100
                cur_dist = 10 * (math.tan(math.radians(prev_angle)) - math.tan(math.radians(angle)))

                cur_speed = (cur_dist)/cap_rate;
                # print cur_dist

                road_width = get_road_width(angle)
                width_increment = road_width/20
                orig = box.copy()
                sorted_box = np.sort(orig)


                lc = 0
                rc = 0

                for x in range(20):
                    for p in sorted_box[2:]:
                        for j in range(4):
                            if orig[j][0] == p[0]:
                                orig[j][0] += width_increment
                                p[0] += width_increment
                                break

                    cv2.drawContours(left, [orig], 0, (255, 255, 0), -1)
                    cv2.fillPoly(left, [box], (0, 0, 0))
                    overlap = cv2.bitwise_and(left, display)
                    ov = cv2.findContours(overlap.copy(), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_NONE)[-2]

                    if ov:
                        ov = max(ov, key=cv2.contourArea)
                        if cv2.contourArea(ov) > 1.0:
                            lc = x + 1
                            break

                orig = box.copy()
                sorted_box = np.sort(orig)

                for x in range(20):
                    for p in sorted_box[:2]:
                        for j in range(4):
                            if orig[j][0] == p[0]:
                                orig[j][0] -= width_increment
                                p[0] -= width_increment
                                break

                    cv2.drawContours(right, [orig], 0, (255, 255, 0), -1)
                    cv2.fillPoly(right, [box], (0,0,0))
                    overlap = cv2.bitwise_and(right, display)
                    ov = cv2.findContours(overlap.copy(), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_NONE)[-2]

                    if ov:
                        ov = max(ov, key=cv2.contourArea)
                        if cv2.contourArea(ov) > 1.0:
                            rc = x + 1
                            break


                # print prev_angle, angle

                print lc, rc
                # print deviation


                print "Speed = ",cur_speed, "Accleration = ",(cur_speed - prev_speed) / cap_rate, " Deviation = ", lc, rc

        # cv2.imshow('width_inc', left)
        # cv2.imshow('width_inc2', right)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Speed: " + '%.2f'%(cur_speed*50), (10, 20), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Acc: " + '%.2f'%((cur_speed - prev_speed) / cap_rate *50), (10, 50), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow('frame', frame)
        cv2.imshow('image', fgmask)
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break

# print t_dist
cap.release()
cv2.destroyAllWindows()