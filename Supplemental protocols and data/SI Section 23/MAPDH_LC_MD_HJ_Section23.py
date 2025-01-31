# -*- coding: utf-8 -*-
"""
Created on Thu Aug  5 18:30:10 2021
@author: EliaG
"""

from pycromanager import Bridge
from matplotlib import image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from skimage.color import rgb2gray
from skimage.transform import resize
import time
import skimage.draw as skdraw
import pandas as pd
import os
import cv2
import datetime
import patterning_functions as PF


bridge = Bridge(convert_camel_case=False)
core = bridge.get_core()
core.setAutoShutter(True)
core.setProperty('UserDefinedStateDevice-1','Label','Empty')

h = 684
w = 608
radius = 100


#%% Initialization:
bridge = Bridge(convert_camel_case=False)
core = bridge.get_core()
DMD = core.getSLMDevice()
core.setProperty(DMD,'TriggerType',1)
# core.setSLMPixelsTo(DMD,100) #show all pixels
h = core.getSLMHeight(DMD)
w = core.getSLMWidth(DMD)
core.setProperty('UserDefinedStateDevice-1','Label','Patterning ON (dichroic mirror)')
core.setProperty('UserDefinedStateDevice','Label','BF')
core.setProperty('UserDefinedShutter-1','State',1)
core.setProperty('UserDefinedShutter','State',1)

#h = 684, w = 608
#Channel 4: UV LED
core.setProperty('Mightex_BLS(USB)','mode','NORMAL')
core.setProperty('Mightex_BLS(USB)','channel',1)
core.setProperty(DMD,'AffineTransform.m00',0)
core.setProperty(DMD,'AffineTransform.m01',-0.7988)
core.setProperty(DMD,'AffineTransform.m02',1231.7751)
core.setProperty(DMD,'AffineTransform.m10',1.1149)
core.setProperty(DMD,'AffineTransform.m11',0.0000)
core.setProperty(DMD,'AffineTransform.m12',-904.0098)
#current set: 0-1000
core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0)

#%% Turn Arduino shutter ON:
core.setProperty('Arduino-Shutter','OnOff',1)
#first 0: closest to you, last 0: furthest away
d = {'s1': '00001', 's2': '00010','s3': '000100', 's4': '01000', 's5': '10000'}
d = {'s0': 0, 's1': 1, 's2': 2,'s3': 4, 's4': 8, 's5': 16}
df = pd.Series(data=d)

#%%Functions: 
    
def valve_on(switch):
    # Switch must be something like 's0', 's1', etc.
    core.setProperty('Arduino-Switch','State',int(df.get(switch)))

def valve_off(switch2='s0'):
    core.setProperty('Arduino-Switch','State',int(df.get(switch2)))
    
def valve_timer(switch, wait):
    # Switch must be something like 's0', 's1', etc.
    core.setProperty('Arduino-Switch','State',int(df.get(switch)))
    for m in range(0, wait):
        time.sleep(1)
    valve_off()

def circle_mask_generator(radius = 100):  
    rr,cc = skdraw.circle(h/2,w/2,radius,shape=[h,w])
    mask1 = np.zeros([h,w],dtype='uint8')
    mask1[rr,cc] = 255
    return mask1
    # np.save('circle_mask_'+str(radius)+'radius.npy',mask1)
    # plt.imshow(mask1)
        
def rectangle_mask_generator(side = 100):
    rr,cc = skdraw.rectangle(((h-side)/2,(w-side)/2),extent=(side,side),shape=[h,w])
    mask2 = np.zeros((h,w),dtype='uint8')
    mask2[rr.astype('int'),cc.astype('int')] = 255
    return mask2
    
def mask_rescaler(in1):
    y1 = resize(in1,(h,w/2))
    wpad = int(w/4)
    ypad = np.pad(y1,((0,0),(wpad,wpad)),'constant', constant_values=(0))
    ypad=np.array(ypad,dtype='uint8')
    ypad[ypad==1]=255
    return ypad

def position_list():
    mm = bridge.get_studio()
    pm = mm.positions()
    pos_list = pm.getPositionList()
    numpos = pos_list.getNumberOfPositions()
    np_list = np.zeros((numpos,2))
    for idx in range(numpos):
        pos = pos_list.getPosition(idx)
        stage_pos = pos.get(0)
        np_list[idx,0] = stage_pos.x
        np_list[idx,1] = stage_pos.y          
    return np_list

def patterning(UVexposure,slimage,channel=4,intensity=1000):
    
    core.setSLMImage(DMD,slimage)
    time.sleep(1.5)
    core.setProperty('Mightex_BLS(USB)','channel',channel)
    core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',intensity)
    time.sleep(UVexposure)
    core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0)
    time.sleep(1)
    core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0)

#%% Patterning Shape

# 10X Objective 
# 1 pixel = 0.45 um
# 100 um gel = 100/0.45 = 222 pixels
# CF = 0.45

# 20X UV Objective 
# 1 pixel = 0.28 um
# 100 um rec. gel = 100/0.28 = 357 pixels
# CF = 0.28

# Circle and Objective Parameters
diam = 20
CF = 0.28
diam_conv = diam / CF
draw_circle = circle_mask_generator(radius=(diam_conv / 2))

# Square and Objective Parameters
square_side = 200
CF = 0.28
square_conv = square_side / CF
draw_rectangle = rectangle_mask_generator(side=square_conv)

#%% Inputs
uv_exposure = 0.4
light_pillar = 0.4 # for patterning off/Empty
brightness = 100 #XCite lamp intensity in %
core.setProperty('HamamatsuHam_DCAM','Binning','2x2')

filename = 'MDPatterning_200umGels'
filename_G = 'MDPatterning_200umGels_G'
filename_RG = 'MDPatterning_200umGels_RG'
filename_RGB = 'MDPatterning_200umGels_RGB'
filename_nacl = 'MDPatterning_200umGels_nacl'
exposure = (0, 100, 100, 100, 10) #exposure in ms
fluorophore = ("skip", 'GFP-FAM','Cy3','Cy5', 'BF') #Fluorophore to use
#          Green Red   Blue   Wash  Wash  NaCl
 valves = ('s0', 's1', 's2', 's3', 's4', 's5')

#%% Setup
xy_up = position_list()
SLim = mask_rescaler(output)
core.setSLMImage(DMD,SLim)
core.setProperty('Mightex_BLS(USB)','channel',1)
core.setProperty('Mightex_BLS(USB)','normal_CurrentSet', 0)


#%% Single-domain Patterning

print('Starting green pregel flow 90 seconds' %stage)
valve_timer(valves[0], 90) #flows pregel 90 seconds 
        
print('Beginning patterning')
core.setProperty('DTOL-DAC-0', 'Volts', light_pillar)
core.setProperty('UserDefinedStateDevice-1','Label','Patterning ON (dichroic mirror)')
core.setProperty('UserDefinedStateDevice','Label','BF')
core.setProperty('UserDefinedShutter-1','State',1)
core.setProperty('UserDefinedShutter','State',1)

for i in range(0,len(xy_up)):   
    core.setXYPosition(xy_up[i,0],xy_up[i,1]) #move to first location
    time.sleep(3) #wait at least 1 second for microscope to reach location
    SLim = mask_rescaler(rectangle_mask_generator(side=(200 / 0.28)))
    patterning(uv_exposure,SLim,channel=4,intensity=1000)

    print('Patterning ended, starting 30 second wash')
    valve_timer(valves[3], 30) #flows buffer 30 seconds
       
    print('Wash ended, beginning imaging')  
    core.setProperty('UserDefinedStateDevice-1','Label','Empty')
    core.setProperty('UserDefinedShutter-1','State',1)
    core.setProperty('UserDefinedShutter','State',1)
    
    for i in range(len(fluorophore)):
        if fluorophore[i] == "skip":
            continue
        if fluorophore[i] == "BF":
            core.setProperty('DTOL-DAC-0', 'Volts', light_pillar_intensity)
            core.setProperty('XCite-Exacte','Lamp-Intensity', 10)
        else:
            core.setProperty('DTOL-DAC-0', 'Volts', 0)
            core.setProperty('XCite-Exacte','Lamp-Intensity', brightness)
        core.setProperty('UserDefinedStateDevice','Label',fluorophore[i])
        core.setExposure(exposure[i])
        time.sleep(3)
        core.snapImage()
        tagged_image = core.getTaggedImage()
        pixels = np.reshape(tagged_image.pix,newshape=[tagged_image.tags['Height'], tagged_image.tags['Width']])
       
        cv2.imwrite(filename_G + '_' + str(fluorophore[i])+'.tif', pixels.astype(np.uint16) )
        core.setProperty('DTOL-DAC-0', 'Volts', 0)
        time.sleep(2)
        core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0) #Redundant UV LED turn-off command

print('Starting red pregel flow 90 seconds' %stage)
valve_timer(valves[1], 90) #flows pregel 90 seconds 
        
print('Beginning patterning')
core.setProperty('DTOL-DAC-0', 'Volts', light_pillar)
core.setProperty('UserDefinedStateDevice-1','Label','Patterning ON (dichroic mirror)')
core.setProperty('UserDefinedStateDevice','Label','BF')
core.setProperty('UserDefinedShutter-1','State',1)
core.setProperty('UserDefinedShutter','State',1)

for i in range(0,len(xy_up)):   
    core.setXYPosition(xy_up[i,0],xy_up[i,1]) #move to first location
    core.setRelativeXYPosition(-90.0, 0)
    patterning(uv_exposure,SLim,channel=4,intensity=1000)

    print('Patterning ended, starting 30 second wash')
    valve_timer(valves[3], 30) #flows buffer 30 seconds
       
    print('Wash ended, beginning imaging')  
    core.setProperty('UserDefinedStateDevice-1','Label','Empty')
    core.setProperty('UserDefinedShutter-1','State',1)
    core.setProperty('UserDefinedShutter','State',1)
    
    for i in range(len(fluorophore)):
        if fluorophore[i] == "skip":
            continue
        if fluorophore[i] == "BF":
            core.setProperty('DTOL-DAC-0', 'Volts', light_pillar_intensity)
            core.setProperty('XCite-Exacte','Lamp-Intensity', 10)
        else:
            core.setProperty('DTOL-DAC-0', 'Volts', 0)
            core.setProperty('XCite-Exacte','Lamp-Intensity', brightness)
        core.setProperty('UserDefinedStateDevice','Label',fluorophore[i])
        core.setExposure(exposure[i])
        time.sleep(3)
        core.snapImage()
        tagged_image = core.getTaggedImage()
        pixels = np.reshape(tagged_image.pix,newshape=[tagged_image.tags['Height'], tagged_image.tags['Width']])
       
        cv2.imwrite(filename_RG + '_' + str(fluorophore[i])+'.tif', pixels.astype(np.uint16) )
        core.setProperty('DTOL-DAC-0', 'Volts', 0)
        time.sleep(2)
        core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0) #Redundant UV LED turn-off command

print('Starting blue pregel flow 90 seconds' %stage)
valve_timer(valves[2], 90) #flows pregel 90 seconds 
        
print('Beginning patterning')
core.setProperty('DTOL-DAC-0', 'Volts', light_pillar)
core.setProperty('UserDefinedStateDevice-1','Label','Patterning ON (dichroic mirror)')
core.setProperty('UserDefinedStateDevice','Label','BF')
core.setProperty('UserDefinedShutter-1','State',1)
core.setProperty('UserDefinedShutter','State',1)

for i in range(0,len(xy_up)):   
    core.setXYPosition(xy_up[i,0],xy_up[i,1]) #move to first location
    core.setRelativeXYPosition(90.0, 0)
    patterning(uv_exposure,SLim,channel=4,intensity=1000)

    print('Patterning ended, starting 30 second wash')
    valve_timer(valves[4], 30) #flows buffer 30 seconds
       
    print('Wash ended, beginning imaging')  
    core.setProperty('UserDefinedStateDevice-1','Label','Empty')
    core.setProperty('UserDefinedShutter-1','State',1)
    core.setProperty('UserDefinedShutter','State',1)
    
    for i in range(len(fluorophore)):
        if fluorophore[i] == "skip":
            continue
        if fluorophore[i] == "BF":
            core.setProperty('DTOL-DAC-0', 'Volts', light_pillar_intensity)
            core.setProperty('XCite-Exacte','Lamp-Intensity', 10)
        else:
            core.setProperty('DTOL-DAC-0', 'Volts', 0)
            core.setProperty('XCite-Exacte','Lamp-Intensity', brightness)
        core.setProperty('UserDefinedStateDevice','Label',fluorophore[i])
        core.setExposure(exposure[i])
        time.sleep(3)
        core.snapImage()
        tagged_image = core.getTaggedImage()
        pixels = np.reshape(tagged_image.pix,newshape=[tagged_image.tags['Height'], tagged_image.tags['Width']])
       
        cv2.imwrite(filename_RG + '_' + str(fluorophore[i])+'.tif', pixels.astype(np.uint16) )
        core.setProperty('DTOL-DAC-0', 'Volts', 0)
        time.sleep(2)
        core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0) #Redundant UV LED turn-off command

        PF.valve_timer(valves[5], 60 ) #flows wash solution for 60 seconds to dissociate sacrificial layer.
        print('Flowing in NaCl')
        time.sleep(60) 

    print('NaCl flow ended, beginning imaging')  
    for i in range(len(fluorophore)):
        if fluorophore[i] == "skip":
    continue
        if fluorophore[i] == "BF":
            core.setProperty('DTOL-DAC-0', 'Volts', light_pillar_intensity)
            core.setProperty('XCite-Exacte','Lamp-Intensity', 10)
        else:
            core.setProperty('DTOL-DAC-0', 'Volts', 0)
            core.setProperty('XCite-Exacte','Lamp-Intensity', brightness)
        core.setProperty('UserDefinedStateDevice','Label',fluorophore[i])
        core.setExposure(exposure[i])
        time.sleep(3)
        core.snapImage()
        tagged_image = core.getTaggedImage()
        pixels = np.reshape(tagged_image.pix,newshape=[tagged_image.tags['Height'], tagged_image.tags['Width']])
       
        cv2.imwrite(filename_w + '_' + str(fluorophore[i])+'.tif', pixels.astype(np.uint16) )
        core.setProperty('DTOL-DAC-0', 'Volts', 0)
        time.sleep(2)

time.sleep(3600)
# core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0) #Redundant UV LED turn-off command
print('Flowing out free-floating hydrogels')  
valve_timer(valves[4], 30) #flows wash solution for 30 seconds after patterning is over.