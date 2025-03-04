from __future__ import annotations
from typing import Tuple, Dict, List, TypedDict
from numpy.typing import NDArray

from Element import *
from Quaternion import *
from MotorManager import *


DEGREES_TO_RADIANS = np.pi / 180.0
RADIANS_TO_DEGREES = 180.0 / np.pi


class ThrustVectorController:
  _instance = None
  
  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance
  
  def __init__(self, motor_manager: MotorManager, max_refresh_speed: float = 270.0):
    """ this is a singleton object to manage a motor contruction

    Args:
        motor_manager (MotorManager): MotorManager class object with a motor type defined
        max_refresh_speed (float, optional): maximum servo rate in degrees/second. Defaults to 270.0 deg/sec.
    """
    if not hasattr(self, "initialized"):
      self.initialized = True
      self.motor_manager = motor_manager
      self.burn_time = motor_manager.burn_time
      self.thetax, self.thetay = 0.0, 0.0
      self.targetx, self.targety = 0.0, 0.0
      self.max_speed = max_refresh_speed * np.pi / 180.0 # rad/s
      self.q = Quaternion(default=True)
      self.offset = np.array([0.0, 0.0, 0.0])
    else:
      pass
  
  def step(self, dt: float) -> None:
    """ update the servo positions according to their maximum response rates for realistic servo modeling

    Args:
        dt (float): small time step since last time step
    """
    epsilon = self.max_speed * dt
    errorx = self.targetx - self.thetax
    errory = self.targety - self.thetay
    # the problem without these if statements is that oscillations occur when perfect accuracy is unattainable - which is always the case
    if abs(errorx) > epsilon:
      self.thetax += np.sign(errorx) * epsilon
    else:
      self.thetax = self.targetx
    
    if abs(errory) > epsilon:
      self.thetay += np.sign(errory) * epsilon
    else:
      self.thetay = self.targety
    
  def moveToMotor(self, offset: NDArray) -> None:
    """ sets the offset parameter to correctly compute the cross product between thrust vector and center of mass position vector

    Args:
        offset (NDArray): relative position of the motor in body-centered coordinates
    """
    self.offset = offset
  
  def updateSetpoint(self, targetx: float, targety: float) -> None:
    """ set the target values for the servos

    Args:
        targetx (float): new servo angle in radians
        targety (float): new servo angle in radians
    """
    self.targetx = targetx
    self.targety = targety
  
  def getThrustVector(self, t: float, cg: NDArray) -> Tuple[NDArray, NDArray]:
    """ gets the force and moment generated by the thrust vector mechanism

    Args:
        t (float): current time in seconds

    Returns:
        Tuple[NDArray, NDArray]: the force, torque vectors in body-centered coordinates
    """
    F = self.motor_manager.getThrust(t=t) * np.array([np.sin(self.thetay), -np.sin(self.thetax) * np.cos(self.thetay), np.cos(self.thetax) * np.cos(self.thetay)])
    R = self.offset - cg
    τ = np.cross(R, F)
    return (F, τ)
  
  def getAttitude(self):
    z = np.array([0, 0, -1.0])
    target = np.array([-np.sin(self.thetay), np.sin(self.thetax) * np.cos(self.thetay), -np.cos(self.thetax) * np.cos(self.thetay)])
    angle = np.acos(np.dot(target, z))
    cross = np.cross(z, target)
    return Quaternion(angle_vector=(angle, cross), is_vector=False)

  def forceToTarget(self) -> None:
    """ a helper function for initialization to force the tvc to initial target state
    """
    self.thetax = self.targetx
    self.thetay = self.targety
  
  
__all__ = [
  "ThrustVectorController",
  "DEGREES_TO_RADIANS",
  "RADIANS_TO_DEGREES"
]