package WheelBrakeStpaWalkthrough {
    private import RaamlFullCorpus::STPA::*;

    part def WheelBrakeAssembly;
    part def BrakeControlUnit;
    item def BrakeCommand;

    #ControlStructure
    part wheelBrake : WheelBrakeAssembly;

    #Controller
    part brakeController : BrakeControlUnit;

    #ControlAction
    item applyBrake : BrakeCommand;
}
