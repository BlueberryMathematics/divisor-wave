"""
Special_Functions.py
    The Special functions class is a set of special functions in the complex plane involving infinite products in the
    complex plane. These products are related to the distribution of prime numbers and the Riemann Hypothesis. The
    methods in this class are called by the file Complex_Plotting.py for complex the creation of complex plots.
4/9/2023
@LeoBorcherding
"""

import cmath
import math
import os
import pprint

import mpmath
import numpy as np
import matplotlib.pyplot as plt
import scipy
from scipy import special
from scipy import constants
import re

plt.style.use('dark_background')

# -----------------------------------------------------------------------------------------------------------------
class Special_Functions :
    """
    Special_Functions is a class designed to organize the many complex functions that may want to be graphed with the
    Complex_Plotting Class.
    """
    # -----------------------------------------------------------------------------------------------------------------
    def __init__(self, plot_type):
        """
        Initialization the Special_Functions Object, defines self arg m = desired magnification exponent
        """

        # Regex for identifying product symbols TODO Implement Summation Factory Function
        self.pattern = r'([a-z]+)_\(([a-z]+)=([0-9]+)\)\^\(([a-z]+)\=([0-9]+)\)\s*\[(.*)\]'
        self.im_mag = False  # imaginary magnification flag (used by some transform functions)

        return

    # -----------------------------------------------------------------------------------------------------------------------
    # Product of Sin(x) via Sin(x) product Representation.
    def product_of_sin(self, z, Normalize_type):
        """
        Computes the infinite product of sin(pi*z/n)
        f(x) = ∏_(n=2)^x { abs ( sin(pi*x/n) ) ] ) }
        Args:
            z (complex): A complex number to evaluate.
        Returns:
            (float): The product of sin(pi*z/n).
        """
        # initialize complex components
        z_real = np.real(z)
        z_imag = np.imag(z)
        # initialize scaling coefficients

        #TODO implement coefficent slider range of values which generates a folder of pngs each showcasing the given function with different values of m & beta by iterating over that range,
        # we then will render multiple frames and combine to a gif or mp4 depending on files req or user input.
        if Normalize_type == 'Y':
            # self.m = 0.0125
            # self.beta = 0.0125
            # self.m = 0.005125
            # self.beta = 0.006125
            self.m = 0.0465
            self.beta = 0.178
        else:
            # self.m = 0.0125
            # self.m = 0.005125
            # self.beta = 0.006125
            self.m = 0.0465
            self.beta = 0.178

        # calculate infinite product
        result = abs(np.prod(
            [self.beta * ((z_real) / k) * np.sin(math.pi * (z_real + 1j * z_imag) / k)
                for k in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def product_of_product_representation_for_sin(self, z, Normalize_type):
        """
        Computes the product of the product representation for sin(pi*z/n).
        f(x) = ∏_(k=2)^x (pi*x) ∏_(n=2)^x (1-(x^2)/(k^2)(n^2))
        Args:
            z (complex): A complex number to evaluate.
        Returns:
            (float): The product of the product representation for sin(pi*z/n).
        """

        #pprint.pprint(z)

        #TODO no magnification for bug testing
        z_real = np.real(z)
        z_imag = np.imag(z)

        # pprint.pprint(z_real)
        # pprint.pprint(z_imag)

        #27 is a fun exponent to try
        power_integer = 2

        if Normalize_type == 'Y':
            # self.m = 0.0125
            # self.m = 0.37
            # # m = 0.07
            # # m = 0.37
            # self.beta = 0.078
            # self.m = 0.0125
            self.m = 0.36
            self.beta = 0.1468
        else:
            # self.m = 0.001
            # # self.m = 0.007
            # self.m = 0.0125
            # # self.m = 0.37
            # self.beta = 0.078
            self.m = 0.0125
            self.beta = 0.078

        # calculate the double infinite product via the double for loop
        result = abs(np.prod(
            [self.beta * ( z_real / n) * (((z_real + 1j * z_imag) * math.pi) * np.prod(
                [1 - ( (z_real + 1j * z_imag) ** 2 ) / ((n ** 2) * (k ** 2))
                 for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        # # print function values for bug testing
        # if (z_real % 1 == 0) and (z_imag % 1 == 0):
        #     print(z, ": ", result)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result



    # -----------------------------------------------------------------------------------------------------------------
    def complex_playground_magnification_currated_functions_DEMO(self, z, Normalize_type):
        """ A playground for fine-tuning the complex magnification for each product series.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """
        z_real = np.real(z)
        z_imag = np.imag(z)

        # # check for imaginary magnification
        # if im_mag is True:
        #     imaginary_magnification = z_imag
        # else:
        #     imaginary_magnification = 1

        #TODO === PRODUCT OF PRODUCT REPRESENTATION OF SIN ===
        # if Normalize_type == 'Y':
        #     self.m = 0.36
        #     self.beta = 0.1468
        # else:
        #     self.m = 0.0125
        #     self.beta = 0.078

        #TODO === RIESZ PRODUCT OF COS ===
        if Normalize_type == 'Y':
            self.m = 0.0125
            self.beta = 0.054
        else:
            self.m = 0.0125
            self.beta = 0.054

        #TODO === Product OF SIN ===
        # result = abs(np.prod(
        #     [self.beta * ((z_real) / k) * np.sin(math.pi * (z_real + 1j * z_imag) / k)
        #         for k in range(2, int(z_real) + 1)])) ** (-self.m)

        #TODO === PRODUCT OF PRODUCT REPRESENTATION OF SIN ===
        # result = abs(np.prod(
        #     [self.beta * ( z_real / n) * (((z_real + 1j * z_imag) * math.pi) * np.prod(
        #         [ 1 - pow((( (z_real + 1j * z_imag) ** 2 ) / ( (n ** 2) * (k ** 2) )), (z_real + 1j * z_imag))
        #          for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        #TODO === PRODUCT OF PRODUCT REPRESENTATION OF SIN 2 ===
        # result = abs(np.prod(
        #     [self.beta * ( z_real / n) * (((z_real + 1j * z_imag) * math.pi) * np.prod(
        #         [ 1 - ( (z_real + 1j * z_imag) ** 2 ) / ( (n ** 2) * (k ** 2) )
        #          for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        #TODO === RIESZ PRODUCT OF COS ===
        # result = abs(np.prod(
        #     [pow((1j * z_imag + np.cos(math.pi * (z_real + 1j * z_imag) * n)), 1j * z_imag)
        #         for n in range(2, int(z_real) + 1)])) ** (-self.m)

        #TODO === RIESZ PRODUCT OF COS 2 ===
        # result = abs(np.prod(
        #     [pow(((z_real + 1j * z_imag) + (z_real + 1j * z_imag) * np.cos(math.pi * (z_real + 1j * z_imag) * n)), (z_real + 1j * z_imag))
        #         for n in range(2, int(z_real) + 1)])) ** (-self.m)

        #TODO === RIESZ PRODUCT OF COS 3 ===
        result = abs(np.prod(
            [pow((1j * z_imag + (1j * z_imag) * np.sin(math.pi * (z_real + 1j * z_imag) * n)), 1j * z_imag)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def cos_of_product_of_sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054
        else:
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054

        # normalized double infinite product for loop
        result = np.cos(abs(np.prod([self.beta * (z_real / n) * np.sin(math.pi * (z_real + 1j * z_imag) / n)
                              for n in range(2, int(z_real) + 1)])) ** (-self.m))

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def sin_of_product_of_sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054
        else:
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054

        # normalized double infinite product for loop
        result = np.sin(abs(np.prod([self.beta * (z_real / n) * np.sin(math.pi * (z_real + 1j * z_imag) / n)
                              for n in range(2, int(z_real) + 1)])) ** (-self.m))

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def cos_of_product_of_product_representation_of_sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054
        else:
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054

        # normalized double infinite product for loop
        result = np.cos(abs(np.prod([self.beta * (z_real / n) * (
                (z_real * math.pi + 1j * z_imag * math.pi) * np.prod(
            [1 - ((z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2) for k in range(2, int(z_real) + 1)])) for n in
                                 range(2, int(z_real) + 1)]))) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def sin_of_product_of_product_representation_of_sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054
        else:
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054

        # normalized double infinite product for loop
        result = np.sin(abs(np.prod([self.beta * (z_real / n) * (
                (z_real * math.pi + 1j * z_imag * math.pi) * np.prod(
            [1 - ((z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2) for k in range(2, int(z_real) + 1)])) for n in
                                 range(2, int(z_real) + 1)]))) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Riesz_Product_for_Cos(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """
        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.0125
            self.beta = 0.054
        else:
            self.m = 0.0125
            self.beta = 0.054

        # # check for imaginary magnification
        # if im_mag is True:
        #     imaginary_magnification = z_imag
        # else:
        #     imaginary_magnification = 1

        # calculate infinite product
        result = abs(np.prod(
            [pow((1j * z_imag + np.cos(math.pi * (z_real + 1j * z_imag) * n)), 1j * z_imag)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Riesz_Product_for_Sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054
        else:
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054

        # calculate infinite product
        result = abs(np.prod(
            [1 + np.sin(math.pi * (z_real + 1j * z_imag) * n)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Riesz_Product_for_Tan(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)
        # m = 0.26
        # m = 0.08

        if Normalize_type == 'Y':
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054
        else:
            # self.m = 1
            # self.beta = 1
            self.m = 0.0125
            self.beta = 0.054

        # calculate infinite product
        result = abs(np.prod(
            [1 + np.tan(math.pi * (z_real + 1j * z_imag) * n)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Viete_Product_for_Cos(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.27
            self.beta = 1
        else:
            self.m = 0.07
            self.beta = 1

        #TODO different values for the base of the denominator try 2, 3, 4, 1/2, phi, pi, e, euler-mascheroni
        # scipy.constants.golden

        # calculate infinite product
        result = abs(np.prod(
            [np.cos(math.pi * (z_real + 1j * z_imag) / (2 ** (n)))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        #TODO add conditional statement for normalization of the function,
        # if user norm yes then return norm else return num

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Viete_Product_for_Sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.87
            self.beta = 0.4
        else:
            self.m = 0.87
            self.beta = 1

        # check for imaginary magnification
        # if self.im_mag is True:
        #     imaginary_magnification = z_imag
        # else:
        #     imaginary_magnification = 1

        #TODO different values for the base of the denominator try 2, 3, 4, 1/2, phi, pi, e, euler-mascheroni
        # scipy.constants.golden

        # calculate infinite product
        result = abs(np.prod(
            [np.sin(math.pi * (z_real + 1j * z_imag) / (2 ** (n)))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Viete_Product_for_Tan(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.004
            self.beta = 0.004
        else:
            self.m = 0.007
            self.beta = 0.004

        # # check for imaginary magnification
        # if self.im_mag is True:
        #     imaginary_magnification = z_imag
        # else:
        #     imaginary_magnification = 1

        #TODO different values for the base of the denominator try 2, 3, 4, 1/2, phi, pi, e, euler-mascheroni
        # scipy.constants.golden

        # calculate infinite product
        result = abs(np.prod(
            [np.tan(math.pi * (z_real + 1j * z_imag) / (2 ** (n)))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        #TODO add conditional statement for normalization of the function,
        # if user norm yes then return norm else return num

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Half_Base_Viete_Product_for_Sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.37
            self.beta = 0.07
        else:
            self.m = 0.07
            self.beta = 1

        # # check for imaginary magnification
        # if self.im_mag is True:
        #     imaginary_magnification = z_imag
        # else:
        #     imaginary_magnification = 1

        #TODO different values for the base of the denominator try 2, 3, 4, 1/2, phi, pi, e, euler-mascheroni
        # scipy.constants.golden

        # calculate infinite product
        result = abs(np.prod(
            [np.sin(math.pi * (z_real + 1j * z_imag) / (2 ** (-n)))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        #TODO add conditional statement for normalization of the function,
        # if user norm yes then return norm else return num

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Riesz_Product_for_Tan_and_Prime_indicator_combination(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)
        m = 0.26
        q = 0.08

        if Normalize_type == 'Y':
            self.m = 0.001
            self.beta = 0.07
        else:
            self.m = 0.001
            self.beta = 0.07

        # calculate infinite product
        num = abs(np.prod(
            [1 + np.tan(math.pi * (z_real + 1j * z_imag) * n)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        FUNC_B = abs(np.prod(
            [(1 * z_real / n) * ((z_real * math.pi + 1j * z_imag * math.pi) * np.prod(
                [1 - ( (z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2)
                 for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-q)

        norm = num / scipy.special.gamma(num)
        FUNC_B_norm = FUNC_B / scipy.special.gamma(FUNC_B)

        # num_exp = FUNC_B_norm ** norm
        # num_exp = norm ** FUNC_B_norm
        # num_exp = norm/FUNC_B_norm
        num_exp = np.cos(FUNC_B_norm/norm)

        return num_exp

    # -----------------------------------------------------------------------------------------------------------------
    def Nested_roots_product_for_2(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)
        # m = 0.26
        # q = 0.08
        m = -1

        if Normalize_type == 'Y':
            self.m = 0.001
            self.beta = 0.07
        else:
            self.m = 0.001
            self.beta = 0.07

        # #TODO Sqrt Sum
        # sum = abs(np.prod(
        #     [ (z_real + 1j * z_imag) ** 2 ** (-n)
        #         for n in range(2, int(z_real) + 1)])) ** (-m)
        # #TODO Sqrt Prod
        # prod = abs(np.sum(
        #     [ (z_real + 1j * z_imag) ** 2 ** (-n)
        #         for n in range(2, int(z_real) + 1)])) ** (-m)

        # #TODO Viete's paradox nest roots sum product representation
        # paradox = abs(np.prod(
        #     [np.sum([( k ** (z_real + 1j * z_imag) ** (-n)) / 2
        #              for k in range(2, int(z_real) + 1)]) for n in range(2, int(z_real) + 1)]))

        #TODO Sqrt Prod
        prod = abs(np.sum(
            [ (z_real + 1j * z_imag) ** 2 ** (-n)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)
        paradox = abs(np.prod(
            [np.prod([(z_real + 1j * z_imag) ** k ** (-n)
                     for k in range(2, int(z_real) + 1)]) for n in range(2, int(z_real) + 1)]))

        # norm = num / scipy.special.gamma(num)
        # FUNC_B_norm = FUNC_B / scipy.special.gamma(FUNC_B)

        # num_exp = FUNC_B_norm ** norm
        # num_exp = norm ** FUNC_B_norm
        # num_exp = norm/FUNC_B_norm
        # num_exp = np.cos(FUNC_B_norm/norm)

        return paradox

    # -----------------------------------------------------------------------------------------------------------------
    def natural_logarithm_of_product_of_product_representation_for_sin(self, z, Normalize_type):
        """
        Computes the natural logarithm of the normalized infinite product of product representation of sin(z).
        f(x) = ln ( ∏_(n=2)^x (pi*x) ∏_(n=2)^x (1-(x^2)/(i^2)(n^2)) )
        Args:
            z (complex): A complex number to evaluate.
            m (float): A constant value for the result.
        Returns:
            (complex): The natural logarithm of the normalized infinite product of product representation of sin(z).
        """
        z_real = np.real(z)
        z_imag = np.imag(z)

        # check for imaginary magnification
        if self.im_mag is True:
            imaginary_magnification = z_imag
        else:
            imaginary_magnification = 1

        # calculate the infinite product
        result = abs(np.prod(
            [self.beta * (z_real * imaginary_magnification / n) * ((z_real * math.pi + 1j * z_imag * math.pi) * np.prod(
                [1 - ((z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2)
                 for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        # take the logarithm
        log_result = cmath.log(result)

        #log_result=cmath.log(result) # scipy.special.gamma(
        #return result / np.log(z)

        # if Normalize_type == 'Y':
        #     result = result / scipy.special.gamma(result)
        # else:
        #     result = result

        return log_result

    # -----------------------------------------------------------------------------------------------------------------
    def gamma_of_product_of_product_representation_for_sin(self, z, Normalize_type):
        """
        Args:
        Returns:
        """
        z_real = np.real(z)
        z_imag = np.imag(z)

        # check for imaginary magnification
        if self.im_mag is True:
            imaginary_magnification = z_imag
        else:
            imaginary_magnification = 1

        result = abs(np.prod(
            [self.beta * (z_real * imaginary_magnification / n) * ((z_real * math.pi + 1j * z_imag * math.pi) * np.prod(
                [1 - ((z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2)
                 for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)
        #TODO FUNCTION TRANSFORMATION SELECTOR
        # right now there are multiple methods for what is a graphing technique of transforming the product with logs and factorials.
        gamma_result = scipy.special.gamma(result)
        #log_result=cmath.log(result) # scipy.special.gamma(

        # if Normalize_type == 'Y':
        #     result = result / scipy.special.gamma(result)
        # else:
        #     result = result

        return gamma_result

    # -----------------------------------------------------------------------------------------------------------------
    def gamma_form_product_of_product_representation_for_sin(self, z, Normalize_type):
        """
        Computes the product of the product representation for sin(z).
         z / [Γ(z) * Γ(1-z)] * e^(-γz^2) * ∏_(n=2)^(∞) e^(z^2 / n^2)
        Args:
            z (complex): A complex number to evaluate.
            m (float): A constant value for the result.
        Returns:
            (float): The product of the product representation for sin(z).
        """

        if Normalize_type == 'Y':
            self.m = 0.0125
            self.beta = 0.054
        else:
            self.m = 0.0125
            self.beta = 0.054

        Euler_mascheroni = 0.57721566490153286060651209008240243104215933593992359880
        z_real = np.real(z)
        z_imag = np.imag(z)
        result = abs(np.prod(
            [self.beta * (z_imag * z_real / n) * scipy.special.gamma(z_real + 1j * z_imag)
                * scipy.special.gamma(1 - (z_real + 1j * z_imag))
                    * cmath.exp((-((z_real + 1j * z_imag) ** 2))) * np.prod(
                        [(cmath.exp(((z_real + 1j * z_imag)**2/(n**2)*(k**2))))
                            for k in range(2, int(z_real) + 1)]) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            result = result / scipy.special.gamma(result)
        else:
            result = result

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Log_power_base_Viete_Product_for_Sin(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.001
            self.beta = 0.07
        else:
            self.m = 0.001
            self.beta = 0.07

        # check for imaginary magnification
        if self.im_mag is True:
            imaginary_magnification = z_imag
        else:
            imaginary_magnification = 1

        #TODO different values for the base of the denominator try 2, 3, 4, 1/2, phi, pi, e, euler-mascheroni
        # scipy.constants.golden

        # calculate infinite product
        num = 1 + abs(np.prod(
            [np.sin(math.pi * (z_real + 1j * z_imag) / (2 ** ((1/n)*np.log((z_real + 1j * z_imag)))))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        den = 1 + abs(np.prod(
            [np.sin(math.pi * (z_real + 1j * z_imag) / (2 ** ((1/n)*np.log((z_real + 1j * z_imag)))))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)
        #THis doesnt really need to start at 2, it could start at 1
        norm = num / scipy.special.gamma(den)

        #TODO add conditional statement for normalization of the function,
        # if user norm yes then return norm else return num

        return norm

    # -----------------------------------------------------------------------------------------------------------------
    def Custom_Riesz_Product_for_Tan(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.001
            self.beta = 0.07
        else:
            self.m = 0.001
            self.beta = 0.07

        # check for imaginary magnification
        if self.im_mag is True:
            imaginary_magnification = z_imag
        else:
            imaginary_magnification = 1

        # calculate infinite product
        num = abs(np.prod(
            [1 + np.tan(math.pi * (z_real + 1j * z_imag) * n)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        den = abs(np.prod(
            [1 + np.tan(math.pi * (z_real + 1j * z_imag) * n)
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        norm = num / scipy.special.gamma(den)

        return norm

    # -----------------------------------------------------------------------------------------------------------------
    def Custom_Viete_Product_for_Cos(self, z, Normalize_type):
        """ A method to multiply two infinite products.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.m = 0.001
            self.beta = 0.07
        else:
            self.m = 0.001
            self.beta = 0.07

        # check for imaginary magnification
        if self.im_mag is True:
            imaginary_magnification = z_imag
        else:
            imaginary_magnification = 1

        #TODO different values for the base of the denominator try 2, 3, 4, 1/2, phi, pi, e, euler-mascheroni
        # scipy.constants.golden

        # calculate infinite product
        num = abs(np.prod(
            [1 + np.cos(math.pi * (z_real + 1j * z_imag) / (z_real ** (n)))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)

        den = abs(np.prod(
            [1 + np.cos(math.pi * (z_real + 1j * z_imag) / (z_real ** (n)))
                for n in range(2, int(z_real) + 1)])) ** (-self.m)
        #THis doesnt really need to start at 2, it could start at 1
        norm = num / scipy.special.gamma(den)

        #TODO add conditional statement for normalization of the function,
        # if user norm yes then return norm else return num

        return norm

    # -----------------------------------------------------------------------------------------------------------------
    def Binary_Output_Prime_Indicator_Function_H(self, z, Normalize_type):
        """ A method to combine two infinite products to produce a prime binary output.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.c = 0.13
            self.m = 0.29

            self.alpha = 0.14
            self.beta = 0.25
        else:
            self.c = 0.83
            self.m = 0.029

            self.alpha = 0.74
            self.beta = 0.025

        # calculate infinite product
        single_prod = abs(np.prod(
            [self.alpha * ((z_real) / k) * np.sin(math.pi * (z_real + 1j * z_imag) / k)
                for k in range(2, int(z_real) + 1)])) ** (-self.c)

        # calculate the double infinite product via the double for loop
        double_prod = abs(np.prod(
            [self.beta * ( z_real / n) * (((z_real + 1j * z_imag) * math.pi) * np.prod(
                [1 - ( (z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2)
                 for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            norm1 = single_prod / scipy.special.gamma(single_prod)
            norm2 = double_prod / scipy.special.gamma(double_prod)
            result = pow(norm1, norm2)
        else:
            result = pow(single_prod, double_prod)

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Prime_Output_Indicator_J(self, z, Normalize_type):
        """ A method to combine two infinite products to produce a prime binary output.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """
        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.c = 0.13
            self.m = 0.29

            self.alpha = 0.14
            self.beta = 0.25
        else:
            self.c = 0.83
            self.m = 0.029

            self.alpha = 0.74
            self.beta = 0.025

        # calculate infinite product
        single_prod_1 = abs(np.prod(
            [self.alpha * ((z_real) / k) * np.sin(math.pi * (z_real + 1j * z_imag) / k)
             for k in range(2, int(z_real) + 1)])) ** (-self.c)

        # calculate infinite product
        single_prod_2 = abs(np.prod(
            [self.alpha * ((z_real) / k) * np.sin(math.pi * (z_real + 1j * z_imag) / k)
             for k in range(2, int(z_real) + 1)])) ** (-self.c)

        # calculate the double infinite product via the double for loop
        double_prod = abs(np.prod(
            [self.beta * (z_real / n) * (((z_real + 1j * z_imag) * math.pi) * np.prod(
                [1 - ((z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2)
                 for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            norm1 = single_prod_1 / scipy.special.gamma(single_prod_1)
            norm2 = single_prod_2 / scipy.special.gamma(single_prod_2)
            norm3 = double_prod / scipy.special.gamma(double_prod)
            result = pow(norm1, pow(norm2, norm3))
        else:
            result = pow(single_prod_1, pow(single_prod_2, double_prod))

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def BOPIF_Q_Alternation_Series(self, z, Normalize_type):
        """ A method to combine two infinite products to produce a prime binary output.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.c = 0.13
            self.m = 0.29

            self.alpha = 0.14
            self.beta = 0.25
        else:
            self.c = 0.83
            self.m = 0.029

            self.alpha = 0.74
            self.beta = 0.025

        # calculate the product of sin
        single_prod = abs(np.prod(
            [self.alpha * ((z_real) / k) * np.sin(math.pi * (z_real + 1j * z_imag) / k)
                for k in range(2, int(z_real) + 1)])) ** (-self.c)

        # calculate the product of the product representation of sin
        double_prod = abs(np.prod(
            [self.beta * ( z_real / n) * (((z_real + 1j * z_imag) * math.pi) * np.prod(
                [1 - ( (z_real + 1j * z_imag) ** 2) / (n ** 2 * k ** 2)
                 for k in range(2, int(z_real) + 1)])) for n in range(2, int(z_real) + 1)])) ** (-self.m)

        # calculate the alternation series Q with H
        alternation \
            = abs(np.prod(
            [ pow((-1), abs(np.prod(
                [pow((-2), self.Binary_Output_Prime_Indicator_Function_H(z, Normalize_type))
                    for s in range(2, int(z_real) + 1)])) ** (-self.c) )
                        for q in range(2, int(z_real) + 1)])) ** (-self.m)

        if Normalize_type == 'Y':
            norm1 = single_prod / scipy.special.gamma(single_prod)
            norm2 = double_prod / scipy.special.gamma(double_prod)
            norm_alternation = alternation / scipy.special.gamma(alternation)
            result = pow(norm1, norm2)
        else:
            result = pow(single_prod, double_prod)

        return result

    # -----------------------------------------------------------------------------------------------------------------
    def Dirichlet_Eta_Derived_From_BOPIF(self, z, Normalize_type):
        """ A method to combine two infinite products to produce a prime binary output.
        Args:
            z: Complex z which isn't converted to z_real & z_imag in this method
            beta: magnification value as the lead coefficient
            m: exponential magnification coefficient
        """

        z_real = np.real(z)
        z_imag = np.imag(z)

        if Normalize_type == 'Y':
            self.c = 0.13
            self.m = 0.29

            self.alpha = 0.14
            self.beta = 0.25
        else:
            self.c = 0.83
            self.m = 0.029

            self.alpha = 0.74
            self.beta = 0.025

        eta_prod = abs(np.prod(
            [ (1 / ( 1 + self.BOPIF_Q_Alternation_Series(z, Normalize_type) * self.Prime_Output_Indicator_J(z, Normalize_type) ) )
             for k in range(2, int(z_real) + 1)])) ** (-self.c)

        return eta_prod


    # -----------------------------------------------------------------------------------------------------------------
    def product_factory(self, product_string_arg):
        """
        Args:
            product_string_arg: regex Collected Function
        Returns:
             product_function_from_string: The function converted to code
        """
        match = re.search(self.pattern, product_string_arg)
        if match is None:
            raise ValueError("Invalid formula")

        var1, start1, var2, end2, prod = match.groups()
        start1, end2 = int(start1), int(end2)

        # Create New Product From User String
        def product_function_from_string(z, m):
            z_real = np.real(z)
            z_imag = np.imag(z)
            prod_with_z = prod.replace('z', '(z_real + 1j*z_imag)')
            result = abs(np.prod(
                [(z_imag * z_real / n) * ((z_real * math.pi + 1j * z_imag * math.pi) * np.prod(
                    [eval(prod_with_z) for k in range(start1, end2 + 1)])) for n in range(start1, end2 + 1)])) ** (-m)
            return result

        # Return the Newly created Product Function
        return product_function_from_string

    # -----------------------------------------------------------------------------------------------------------------
    def lamda_function_library(self, Normalize_type, selection=None):
        """
        Args:
            None, will eventually be user_input
        Colorization:
        """
        # The function product_of_product_representation_for_sin and Custom_Function are identical however
        # Custom_Function is multiplied by an imaginary scalar for magnification
        # TODO fix the product_factory function, currently broken but will allow users to design their own functions

        # lamda library
        operations = {

            # Library Selection for Complex Analysis of Holomorphic & Meromorphic functions:
            # Todo Special Infinite Products section

            # Todo Basic library of functions
            '1': lambda z: self.product_of_sin(z, Normalize_type),
            '2': lambda z: self.product_of_product_representation_for_sin(z, Normalize_type),
            '3': lambda z: self.product_of_product_representation_for_sin_COMPLEX_VARIANT(z, Normalize_type),
            '4': lambda z: self.complex_playground_magnification_currated_functions_DEMO(z, Normalize_type),

            '5': lambda z: self.Riesz_Product_for_Cos(z, Normalize_type),
            '6': lambda z: self.Riesz_Product_for_Sin(z, Normalize_type),
            '7': lambda z: self.Riesz_Product_for_Tan(z, Normalize_type),

            '8': lambda z: self.Viete_Product_for_Cos(z, Normalize_type),
            '9': lambda z: self.Viete_Product_for_Sin(z, Normalize_type),
            '10': lambda z: self.Viete_Product_for_Tan(z, Normalize_type),

            '11': lambda z: self.cos_of_product_of_sin(z, Normalize_type),
            '12': lambda z: self.sin_of_product_of_sin(z, Normalize_type),
            '13': lambda z: self.cos_of_product_of_product_representation_of_sin(z, Normalize_type),
            '14': lambda z: self.sin_of_product_of_product_representation_of_sin(z, Normalize_type),

            '15': lambda z: self.Binary_Output_Prime_Indicator_Function_H(z, Normalize_type),
            '16': lambda z: self.Prime_Output_Indicator_J(z, Normalize_type),
            '17': lambda z: self.BOPIF_Q_Alternation_Series(z, Normalize_type),
            '18': lambda z: self.Dirichlet_Eta_Derived_From_BOPIF(z, Normalize_type),

            '19': lambda z: abs(mpmath.loggamma(z)),
            '20': lambda z: 1 / (1 + z ^ 2),
            '21': lambda z: abs(z ** z),
            '22': lambda z: mpmath.gamma(z),

            # Todo User Function Utilities
            '23': lambda z: self.natural_logarithm_of_product_of_product_representation_for_sin(z, Normalize_type),
            '24': lambda z: self.gamma_of_product_of_product_representation_for_sin(z, Normalize_type),
            '25': lambda z: self.gamma_form_product_of_product_representation_for_sin(z, Normalize_type),

            '26': lambda z: self.Custom_Riesz_Product_for_Tan(z, Normalize_type),
            '27': lambda z: self.Custom_Viete_Product_for_Cos(z, Normalize_type),
            '28': lambda z: self.Half_Base_Viete_Product_for_Sin(z, Normalize_type),
            '29': lambda z: self.Log_power_base_Viete_Product_for_Sin(z, Normalize_type),
            '30': lambda z: self.Riesz_Product_for_Tan_and_Prime_indicator_combination(z, Normalize_type),

            '31': lambda z: self.Nested_roots_product_for_2(z, Normalize_type),
            '32': lambda z: self.product_factory("∏_(n=2)^z [pi*z ∏_(k=2)^z (1 - z^2 / (k^2 * n^2))]", Normalize_type, )
        }

        Catalog = {
            # Todo Special Infinite Products section

            '1': 'product_of_sin(z, Normalize_type)',
            '2': 'product_of_product_representation_for_sin(z, Normalize_type)',
            '3': 'product_of_product_representation_for_sin_COMPLEX_VARIANT(z, Normalize_type)',
            '4': 'complex_playground_magnification_currated_functions_DEMO(z, Normalize_type)',

            '5': 'Riesz_Product_for_Cos(z, Normalize_type)',
            '6': 'Riesz_Product_for_Sin(z, Normalize_type)',
            '7': 'Riesz_Product_for_Tan(z, Normalize_type)',

            '8': 'Viete_Product_for_Cos(z, Normalize_type)',
            '9': 'Viete_Product_for_Sin(z, Normalize_type)',
            '10': 'Viete_Product_for_Tan(z, Normalize_type)',

            '11': 'cos_of_product_of_sin(z, Normalize_type)',
            '12': 'sin_of_product_of_sin(z, Normalize_type)',
            '13': 'cos_of_product_of_product_representation_of_sin(z, Normalize_type)',
            '14': 'sin_of_product_of_product_representation_of_sin(z, Normalize_type)',

            '15': 'Binary_Output_Prime_Indicator_Function_H(z, Normalize_type)',
            '16': 'Prime_Output_Indicator_J(z, Normalize_type)',
            '17': 'BOPIF_Q_Alternation_Series(z, Normalize_type)',
            '18': 'Dirichlet_Eta_Derived_From_BOPIF(z, Normalize_type)',

            '19': 'BASIC: abs(mpmath.loggamma(z))',
            '20': 'BASIC: 1 / (1 + z ^ 2)',
            '21': 'BASIC: abs(z ** z)',
            '22': 'BASIC: mpmath.gamma(z)',

            # Todo User Function Utilities
            '23': 'natural_logarithm_of_product_of_product_representation_for_sin(z, Normalize_type)',
            '24': 'gamma_of_product_of_product_representation_for_sin(z, Normalize_type)',
            '25': 'gamma_form_product_of_product_representation_for_sin(z, Normalize_type)',

            '26': 'Custom_Riesz_Product_for_Tan(z, Normalize_type)',
            '27': 'Custom_Viete_Product_for_Cos(z, Normalize_type)',
            '28': 'Half_Base_Viete_Product_for_Sin(z, Normalize_type)',
            '29': 'Log_power_base_Viete_Product_for_Sin(z, Normalize_type)',
            '30': 'Riesz_Product_for_Tan_and_Prime_indicator_combination(z, Normalize_type)',

            '31': 'Nested_roots_product_for_2(z, Normalize_type)',
            '32': 'product_factory("∏_(n=2)^z [pi*z ∏_(k=2)^z (1 - z^2 / (k^2 * n^2))]", Normalize_type, )'
        }

        # When called programmatically, skip the interactive prompt
        if selection is not None:
            if str(selection) in operations:
                return operations[str(selection)]
            raise ValueError(f"Invalid function selection: {selection}. Must be 1-32.")

        print("Please Select a Function to plot:")
        for key, value in Catalog.items():
            print(f'{key}: {value}')

        while True:
            user_input = input('Enter your choice: ')
            if user_input in operations:
                return operations[user_input]
            else:
                print("Invalid choice. Please try again.")

        return operations[f'{user_input}']