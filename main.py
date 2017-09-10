import numpy as np
import cv2
import math

frame = None

# 320 60

name = "right.mp4"
f = open("log.log", "w+")

next = 20

def get_safe_width(angle):
    return -0.5 * angle + 55

def get_road_width(angle):
    if name == "zigzag.mp4":
        return (-20) * angle + 1800
    elif name == "left1.mp4" or name == "speed.mp4":
        return (- 77 / 4) * angle + 3465 / 2
    else:
        return (- 247 / 12) * angle + 3705 / 2

def mycopy(array):
    li = []
    for i in array:
        li.append([int(i[0]), int(i[1])])
    return np.array(li)


cap = cv2.VideoCapture(name)
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
delta_dev = 0

cap_rate = 6

speed_flag = False
deviation_flag = False
deceleration_flag = False

speed_threshold = 50
deviation_threshold = 13
deceleration_threshold = -3

ret, frame = cap.read()


while True:

    ret, frame = cap.read()
    if not ret:
        break

    edges = cv2.Canny(frame, 100, 200)
    display = edges.copy()
    i += 1

    fgmask = fgbg.apply(frame)
    fgmask = cv2.erode(fgmask, None, iterations=2)
    fgmask = cv2.dilate(fgmask, None, iterations=2)

    left = np.zeros(fgmask.shape, np.uint8)
    right = np.zeros(fgmask.shape, np.uint8)

    if fgmask.any():

        cnts = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
        if cnts:
            c = max(cnts, key=cv2.contourArea)
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
                deviation = lc -rc
                delta_dev = deviation - prev_deviation
                prev_deviation = deviation

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

                center_x /= 4.0
                center_y /= 4.0

                angle = (60.0 - (((center_y - mid_height) * 1.0)/mid_height * 60.0)) + 30.0

                cur_dist = 10 * (math.tan(math.radians(prev_angle)) - math.tan(math.radians(angle)))

                cur_speed = (cur_dist)/cap_rate;

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

                # orig = box.copy()
                # sorted_box = np.sort(orig)

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

                #deviation = lc - rc

                #print "Speed = ",cur_speed, "Acceleration = ",(cur_speed - prev_speed) / cap_rate, " Deviation = ", lc, rc


        font = cv2.FONT_HERSHEY_SIMPLEX
        if i > 10:
            cv2.putText(frame, "Speed: " + '%.2f'%(cur_speed*50), (10, 20), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "Acc: " + '%.2f'%((cur_speed - prev_speed) / cap_rate *50), (10, 50), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "Dev: " + '%.2f'%((delta_dev)), (10, 80), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)



        if i > 20:
            if cur_speed * 50 > speed_threshold:
                speed_flag = True
                print "hid"
            if delta_dev > deviation_threshold:
                deviation_flag = True
            if (cur_speed - prev_speed) / cap_rate * 50 < deceleration_threshold:
                deceleration_flag = True

            if speed_flag:
                print "hi"
                cv2.putText(frame, "Overspeeding", (500, 20), font, 0.6, (255, 255, 255), 1,
                            cv2.LINE_AA)
                next += 30
            if deviation_flag:
                cv2.putText(frame, "Sudden deviation", (500, 40), font, 0.6, (255, 255, 255), 1,
                            cv2.LINE_AA)
                next += 30
            if deceleration_flag:
                cv2.putText(frame, "Sudden brakes", (500, 60), font, 0.6, (255, 255, 255), 1,
                            cv2.LINE_AA)
                next += 30
        cv2.imshow('frame', frame)

        cv2.imshow('edges', edges)
    k = cv2.waitKey(70)
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()

