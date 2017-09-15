import numpy as np
import cv2
import math

frame = None

# 320 60

f = open("log.log", "w+")

next = 20

def get_safe_width(angle):
    return -0.5 * angle + 55

def get_road_width(name, angle):
    if name == "zigzag_case.mp4":
        return (-20) * angle + 1800
    elif name == "ideal_case.mp4" or name == "speed.mp4":
        return (- 77 / 4) * angle + 3465 / 2
    else:
        return (- 247 / 12) * angle + 3705 / 2

speed_threshold = 44
deviation_threshold = 6
deceleration_threshold = -7
failures = 0

print "Enter speed threshold (recommended 44 to 50): "
speed_threshold = input()
print "Enter deviation threshold (recommended 5 to 8): "
deviation_threshold = input()
print "Enter Deceleration threshold (recommended -8 to -6)"
deceleration_threshold = input()


for name in ["ideal_case.mp4", "right.mp4", "left.mp4", "zigzag_case.mp4"]:
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
    dev = 0
    cnt = 0

    cap_rate = 4

    speed_flag = False
    deviation_flag = False
    deceleration_flag = False

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
                    deviation = lc - rc
                    delta_dev = math.fabs(deviation - prev_deviation)
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

                    iterations = 40
                    road_width = get_road_width(name, angle)
                    width_increment = road_width/iterations
                    orig = box.copy()
                    sorted_box = np.sort(orig)

                    lc = 0
                    rc = 0

                    for x in range(iterations):
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

                        if cv2.countNonZero(overlap) > 6:
                            lc = x + 1
                            break

                    orig = box.copy()
                    sorted_box = np.sort(orig)
                    display = edges.copy()

                    for x in range(iterations):
                        for p in sorted_box[:2]:
                            for j in range(4):
                                if orig[j][0] == p[0]:
                                    orig[j][0] -= width_increment
                                    p[0] -= width_increment
                                    break

                        cv2.drawContours(right, [orig], 0, (255, 255, 0), -1)
                        cv2.fillPoly(right, [box], (0,0,0))
                        overlap = cv2.bitwise_and(right, display)
                        # cv2.imshow("over", overlap)
                        ov = cv2.findContours(overlap.copy(), cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_NONE)[-2]

                        if cv2.countNonZero(overlap) > 6:
                            rc = x + 1
                            break

                    #deviation = lc - rc
                    # print lc / (iterations) * road_width
                    #print "Speed = ",cur_speed, "Acceleration = ",(cur_speed - prev_speed) / cap_rate, " Deviation = ", lc, rc


            font = cv2.FONT_HERSHEY_SIMPLEX
            if i > 15:
                # cnt += 1
                # dev += delta_dev
                delta_dev /= (10 if 'zi' not in name else 1)
                cv2.putText(frame, "Speed: " + '%.2f'%(cur_speed*50), (10, 20), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, "Acc: " + '%.2f'%((cur_speed - prev_speed) / cap_rate *50), (10, 50), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, "Dev: " + '%.2f'%(delta_dev), (10, 80), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)



            if i > 40:
                if cur_speed * 50 > speed_threshold:
                    speed_flag = True
                if delta_dev > deviation_threshold:
                    deviation_flag = True
                if (cur_speed - prev_speed) / cap_rate * 50 < deceleration_threshold:
                    deceleration_flag = True

                if speed_flag:
                    cv2.putText(frame, "Overspeeding", (400, 20), font, 0.6, (255, 255, 255), 1,
                                cv2.LINE_AA)
                    f.write("Overspeeding\n")
                if deviation_flag:
                    cv2.putText(frame, "Sudden deviation", (400, 40), font, 0.6, (255, 255, 255), 1,
                                cv2.LINE_AA)
                    f.write("Sudden deviation\n")
                if deceleration_flag:
                    cv2.putText(frame, "Sudden brakes", (400, 60), font, 0.6, (255, 255, 255), 1,
                                cv2.LINE_AA)
                    f.write("Sudden brakes\n")
            cv2.imshow('Traffic Monitoring', frame)
            # cv2.imshow('mog2', fgmask)
            # cv2.imshow('edges2', edges)
            # cv2.imshow('edges', left)
            # cv2.imshow('edges3', right)
        k = cv2.waitKey(70)
        if k == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    f.write("\n")
    failures += len(filter(lambda x:x, [deceleration_flag, deviation_flag, speed_flag]))
    raw_input()



if failures >= 3:
    print "There is a high possibility for occurance of an accident"
else:
    print "There is a less possibility for occurance of an accident"