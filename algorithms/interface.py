import collections
from abc import ABCMeta, abstractmethod


class AlgorithmInterface:
    """
    Clinical scoring systems to predict organ failure in AP patients. 

    This module includes scoring metric equations as well as helper 
    functions for estimating lab tests, converting units, etc. 
    """
    __metaclass__ = ABCMeta

    required_fields = []
    optional_fields = []

    @classmethod
    def __init__(self, request):
        self.request = request

    @classmethod
    def can_process(self):
        return all([self.request.get(ii) is not None for ii in self.required_fields])

    @classmethod
    def __repr__(self):
        return 'Required parameters: ({})\nOptional parameters: ({})'.format(
            ', '.join(self.required_fields),
            ', '.join(self.optional_fields))

    @classmethod
    def params(self):
        return { "required": self.required_fields,
                 "optional": self.optional_fields}

    @abstractmethod
    def evaluate(self):
        pass

    @classmethod
    def calculate_subscore(self, variable, score_range):
        sr = collections.OrderedDict(sorted(score_range.items()))
        res = None
        for k, v in sr.items():
            if variable >= k:
                res = v
        return res

    @classmethod
    def enforce_lower_bound(self, variable, lower_bound):
        """
        If variable below lower bound, set to None

        Args:
          variable: variable in question, int or float
          lower_bound: int or float

        Returns:
          variable: returns same if above lower bound, else None.
        """
        if variable is not None:
            if variable < lower_bound: 
                variable = None
        return variable

    @classmethod
    def imperial_to_metric(self, height, weight):
        """
        Convert imperial units to metric units for height and weight.

        Returns None if input is None. 

        Args:
          height: height in inches
          weight: weight in pounds

        Returns:
          height: height in meters, or None
          weight: weight in kg, or None
        """
        INCH_TO_METER = 0.0254
        LB_TO_KG = 0.453592
        if height is not None and weight is not None:
            return (height * INCH_TO_METER, weight * LB_TO_KG)
        elif height is not None:
            return (height * INCH_TO_METER, weight)
        elif weight is not None:
            return (height, weight * LB_TO_KG)
        else:
            return (height, weight)

    @classmethod
    def calculate_bmi(self, height, weight, bmi):
        """
        Estimate body mass index from height and weight in metric.

        Args:
          height: height in meters, float
          weight: weight in kg, float
          bmi: body mass index, kg/m^2

        Returns:
          bmi: body mass index, kg/m^2
        """
        if bmi is None:
            if height is not None and weight is not None:
                bmi = weight / height**2
        return bmi

    @classmethod
    def arterialbg_from_pulseox(self, paO2, spO2):
        """
        Imputes PaO2 (from ABG) from SpO2 (from pulse oximeter reading).

        Brown, Samuel M., et al. Critical care medicine 
        45.8 (2017): 1317-1324.

        Args:
          paO2: arterial oxygen partial pressure 
          spO2: SpO2 pulse oximetry measurement

        Returns:
          paO2: real part of nonlinear imputation of PaO2 from SpO2.

        NOTE: May choose not to approximate if PaO2 > 0.96 because
        approximation worsens at edges of sigmoid.
        """
        if paO2 is None:
            if spO2 is not None:
                c1, c2, denominator = 11700, 50, (1/float(spO2) - 1)
                term1 = (
                          (c1 / denominator) + 
                          (c2**3 + (c1 / denominator)**2)**0.5
                        )**(1/3)
                term2 = (
                          (c1 / denominator) - 
                          (c2**3 + (c1 / denominator)**2)**0.5
                        )**(1/3)
                paO2 = (term1 + term2).real
        return paO2

    @classmethod
    def fahrenheit_to_celsius(self, temperature):
        """
        Converts patient temperature from fahrenheit to celsius.

        Args:
          temperature: Temperature in Fahrenheit

        Returns:
          temperature: Temperature in Celsius
        """
        if temperature is not None: temperature = (temperature - 32) / 1.8
        return temperature

    @classmethod
    def glasgow_coma_scale(self, eye_score, verbal_score, motor_score):
        """
        Compute Glasgow Coma Scale based on eye, verbal, and motor response.

        Args:
          eye_score: int, 1= open spontaneously, 2=open to verbal command
            3=open in response to pain, 4=no response
          verbal_score: 1=talk-oriented, 2=confused speech oriented,
            3=inappropriate words, 4=incomprehensible sounds,
            4=no response
          motor_score: 1=obeys commands, 2=localizes pain,
            3=flexion-withdrawal, 4=abnormal flexion,
            5=extension, 6=no response

        Returns:
          glasgow_coma: int, used to assess comma status
        """
        glasgow_coma = None
        if all(v is not None for v in [eye_score, verbal_score, motor_score]):
            glasgow_coma = 0
            if eye_score == 1: glasgow_coma += 4 # Open Spontaneously
            if eye_score == 2: glasgow_coma += 3 # Open to Verbal Command
            if eye_score == 3: glasgow_coma += 2 # Open in response to pain
            if eye_score == 4: glasgow_coma += 1  # No Response
            if verbal_score == 1: glasgow_coma += 5 # Talk-Oriented
            if verbal_score == 2: glasgow_coma += 4 # Confused Speech Disoriented
            if verbal_score == 3: glasgow_coma += 3 # Inappropriate words
            if verbal_score == 4: glasgow_coma += 2  # Incomprehensible sounds
            if verbal_score == 5: glasgow_coma += 1 # No Response
            if motor_score == 1: glasgow_coma += 6 # Obeys Command
            if motor_score == 2: glasgow_coma += 5 # Localizes Pain
            if motor_score == 3: glasgow_coma += 4 # Flexion - Withdrawal
            if motor_score == 4: glasgow_coma += 3  # Abnormal flexion
            if motor_score == 5: glasgow_coma += 2 # Extension
            if motor_score == 6: glasgow_coma += 1 # No Response
        return glasgow_coma