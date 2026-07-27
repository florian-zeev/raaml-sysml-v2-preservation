package PreservationSmoke {
    private import ScalarValues::*;

    doc /*
     * Milestone 0 fixture for the pinned SysML v2 validator.
     */

    enum def ReviewState {
        candidate;
        accepted;
    }

    attribute def SourceAnchor {
        attribute line : Natural[1];
    }

    metadata def PreservedFact {
        ref :>> annotatedElement : SysML::Usage;
        attribute reviewStatus : ReviewState[1];
        attribute anchors : SourceAnchor[0..*];
    }

    part def Node {
        ref related : Node[0..*];
    }

    connection def Trace {
        end source : Node;
        end target : Node;
    }

    part source : Node {
        @PreservedFact {
            reviewStatus = ReviewState::candidate;
        }
    }

    part target : Node;
    connection trace : Trace connect source to target;
}
