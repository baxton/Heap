


import os
import sys
import array
import numpy as np
import scipy as sp
import scipy.io as sio
import ctypes
import datetime as dt

from sklearn.metrics import classification_report

import files
import features


DLL = ctypes.cdll.LoadLibrary("C:\\Temp\\kaggle\\epilepsy\\scripts\\sub5\\dtw_fast.dll")


path = "C:\\Temp\\kaggle\\epilepsy\\data\\"
path_train = path + "prepared_sub5\\"


PREICTAL_CLS = 1
INTERICTAL_CLS = 0

X_LEN = features.READ_LEN


W=600



origin = sp.zeros((X_LEN,), dtype=np.float32)
gen_mean = None
ii_mean = None
pi_mean = None



FILE_IDX  = 0
SEG_IDX   = 1
CLS_IDX   = 2
X_IDX     = 3






def DTWDistance(s1, s2, w, giveup_threshold = float('inf')):
    res = ctypes.c_float(0.)
    code = DLL.DTWDistance(s1.ctypes.data, s2.ctypes.data, ctypes.c_int(s1.shape[0]), ctypes.c_int(s2.shape[0]), ctypes.c_int(w), ctypes.c_float(giveup_threshold), ctypes.addressof(res))
    return res.value


def DTWDistance_BM(s1, s2, w, giveup_threshold):

    N1 = s1.shape[0] + 1
    N2 = s2.shape[0] + 1

    giveup = False

    DTW = sp.zeros((N1, N2), dtype=np.float32)

    w = max(w, abs(len(s1)-len(s2)))

    DTW.fill(float('inf'))
    DTW[0,0] = 0

    for i in range(len(s1)):

        min_dist = float('inf')

        for j in range(max(0, i-w), min(len(s2), i+w)):
            dist= (s1[i]-s2[j])**2

            dtwI = i + 1
            dtwJ = j + 1

            DTW[dtwI, dtwJ] = dist + min(DTW[dtwI-1,dtwJ], DTW[dtwI,dtwJ-1], DTW[dtwI-1,dtwJ-1])

            if min_dist > DTW[dtwI, dtwJ]:
                min_dist = DTW[dtwI, dtwJ]

        if min_dist > giveup_threshold:
            giveup = True
            break

    return min_dist if giveup else DTW[len(s1), len(s2)]



###################################################



###################################################



def distance(s1, s2, giveup_threshold = float('inf')):
##    global memo
##    memo.clear()
##
##    d = LCS(s1, s2, s1.shape[0], s2.shape[0])
##    return 1. / d if d != 0 else float('inf')


    d = DTWDistance(s1, s2, W, giveup_threshold)


    return d



def get_segment(fname):
    if "interictal" in fname:
        return "interictal_segment"
    elif "preictal" in fname:
        return "preictal_segment"

    return"test_segment"


def get_cls(segment):
    if "interictal" in segment:
        return INTERICTAL_CLS

    return PREICTAL_CLS






def get_data_matrix(f, key_word):
    mat = sio.loadmat(f)
    key = [k for k in mat.keys() if key_word in k][0]
    data = mat[key]

    freq = data['sampling_frequency'][0][0][0][0]
    sensors = data['data'][0,0].shape[0]
    length = data['data'][0,0].shape[1]
    length_sec = data['data_length_sec'][0][0][0][0]

    return data['data'][0,0], freq, sensors, length







def read_data():
    data = None

    data_files = [path_train + f for f in os.listdir(path_train)]

    length = features.READ_LEN

    for fn in data_files:
        with open(fn, "r") as fin:
            tmp = np.loadtxt(fin, delimiter=',')
            if None == data:
                data = tmp
            else:
                data = sp.concatenate((data, tmp), axis=0)

    return data.astype(np.float32)





def get_min_distance(data, v):

    min_d = float('inf')
    cls = INTERICTAL_CLS
    f_id = -1
    s_id = -1

    for c in data:
        d = distance(v, c[3:], min_d)
        if min_d > d:
            min_d = d
            f_id = c[0]
            s_id = c[1]
            cls = c[2]

            print "# >>", min_d, cls, "(%d, %d)" % (f_id, s_id)

    return min_d, cls, f_id, s_id



def process(data):

    #########################################################
    ## select test files
    #########################################################

    #test_ii_indices = [381,273,324,416,91,5,172,141,84,88,563,724,634,546,735,864,686,570,759,765,1151,1942,1013,1515,1437,1739,1817,1892,2408,1058,2577,2455,3086,2457,2974,2694,2436,2427,3188,3091,3417,3388,3421,3641,3436,3394,3479,3513,3487,3250,3714,3676,3716,3723,3679,3691,3713,3682,3683,3689,3724,3757,3752,3745,3729,3754,3751,3733,3747,3748]
    #test_pi_indices = [3766,3789,3770,3772,3773,3785,3775,3778,3784,3786,3819,3792,3809,3827,3811,3817,3798,3823,3807,3825,3886,3869,3850,3860,3858,3903,3856,3848,3872,3883,3904,3929,3960,3907,3931,3921,3917,3975,3916,3990,4001,4002,4020,4015,4007,4008,4030,4019,4011,4028,4031,4033,4037,4039,4042,4044,4045,4047,4049,4050,4055,4056,4060,4061,4063,4066]
    test_ii_indices = [424,295,67,340,107,231,134,443,268,171,86,391,220,267,236,345,388,232,88,57,691,800,840,967,509,582,521,620,488,742,755,740,492,577,637,781,496,787,958,782,1874,981,1197,2401,1914,1798,2312,2348,1950,1090,2034,1512,1875,1604,1867,1441,1298,1772,1842,2061,2990,3008,2728,3188,3160,2507,3070,2513,2836,2520,2430,2677,2999,2943,3028,3104,2977,3165,3209,2530,3626,3616,3427,3275,3396,3229,3497,3649,3424,3547,3365,3496,3652,3512,3537,3267,3542,3369,3262,3611,3719,3675,3676,3712,3721,3682,3683,3684,3687,3688,3717,3691,3723,3693,3711,3695,3696,3698,3702,3706,3725,3726,3727,3731,3734,3737,3739,3740,3741,3742,3743,3745,3746,3747,3765,3751,3753,3764,3759,3763]
    test_pi_indices = [3784,3767,3769,3773,3787,3775,3788,3780,3782,3783,3812,3791,3792,3816,3808,3826,3810,3813,3814,3803,3883,3895,3872,3900,3843,3846,3838,3839,3861,3881,3953,3946,3954,3951,3964,3931,3938,3936,3927,3999,4002,4003,4029,4015,4030,4008,4017,4010,4014,4019,4032,4034,4038,4039,4040,4044,4045,4048,4051,4054,4057,4058,4059,4060,4061,4064]
    #########################################################

    y = []
    result = []

    for i in (test_ii_indices + test_pi_indices):
    #for i in (test_pi_indices):
        if i in files.INTERICTAL_FILES:
            fn = files.INTERICTAL_FILES[ i ]
        else:
            fn = files.PREICTAL_FILES[ i ]

        seg = get_segment(fn)
        cls = get_cls(seg)

        y.append(cls)

        data_matrix, freq, sensors, length = get_data_matrix(fn, seg)

        p = 0.
        for s in range(sensors):
            print "# sensor ", s,
            v = features.extract_features( data_matrix[s] )
            l = v.shape[0]
            v1 = v[:l/3]
            v2 = v[l/3:2*l/3]
            v3 = v[2*l/3:]

            d, found_cls1, f_id, s_id = get_min_distance(data, v1)
            d, found_cls2, f_id, s_id = get_min_distance(data, v2)
            d, found_cls3, f_id, s_id = get_min_distance(data, v3)
            c = (found_cls1 + found_cls2 + found_cls3) / 3.
            p += INTERICTAL_CLS if c < .5 else PREICTAL_CLS

        p /= sensors

        print "#%s,%f" % (fn, p)

        v = INTERICTAL_CLS if p < .5 else PREICTAL_CLS
        result.append(v)



    #######
    res = classification_report(y, result)
    print res





def main():
    data = read_data()
    print "# data loaded"
    process(data)



if __name__ == '__main__':
    main()



#
# cat dog_1_result.txt | grep "mat : " | sed 's/.*\(Dog_1.*mat\) : \([10]\)/\1,\2\r\n/' > dog_1_sub.txt
# cat dog_2_result.txt | grep "mat : " | sed 's/.*\(Dog_2.*mat\) : \([10]\)/\1,\2\r\n/' > dog_2_sub.txt
#
#
# for f in `ls -1 ../data/Dog_3/ | grep test_segment`; do python feed_one.py ../data/Dog_3/$f "test_segment" | ./cls_node.exe >> dog_3_result.txt ; done
#