# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 17:08:34 2018

@author: Pavel

Unit tests for the functions contained within the randomLib.turbulence module
"""

import unittest

import numpy as np
import os
os.chdir(os.pardir)
import randomLib.turbulence as tb

class Testturbulence(unittest.TestCase):
    
    def test_generate_noise(self):
        """
        Checking that the returned array is of the right shape
        And contained only values between one and two
        """
        noise = tb.generate_noise(300)
        self.assertEqual((300,300), np.shape(noise))
        for line in noise:
            for value in line:
                self.assertTrue(value>=0 and value<=1)
            
    def test_smoothNoise(self):
        """
        Checking that the returned array is of the right shape
        And contained only values between one and two
        Also checks that the result is actually smoother
        by calculating the variance of the original and smoothened noise
        The variance should be smaller for the smoothened noise
        """
        noise = tb.generate_noise(300)
        sm_noise = tb.smoothNoise(noise,2)
        self.assertEqual((300,300), np.shape(sm_noise))
        for line in sm_noise:
            for value in line:
                self.assertTrue((value>=0 and value<=1))
        self.assertGreaterEqual(np.var(noise), np.var(sm_noise))
    
    def test_turbulence(self):
        """
        Unsure about what parameters to test with.
        N can be anything (we will use 300), 
        D is the number of layers added, between 3 and 8
        initial size is usually between 1 and 4
        The result should be a N*N array of values between 0 and 1
        """
        
        turb = tb.turbulence(300,7,3)
        self.assertEqual((300,300), np.shape(turb))
        for line in turb:
            for value in line:
                #print(value)
                self.assertTrue((value>=0 and value<=1))
        
    def test_turbulence_rgb(self):
        """
        Simillar as above, we can only test the output shape
        and that all the values are normalised between 0 and 1
        """
        turb = tb.turbulence_rgb(300)
        self.assertEqual((300,300,3), np.shape(turb))
        
        for layer in turb:
            for line in layer:
                for value in line:
                    self.assertTrue(value>=0 and value<=1)
                
        

if __name__=='__main__':
    unittest.main()

