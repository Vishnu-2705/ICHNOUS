import React from "react";
import { BaseEdge, EdgeProps, getBezierPath } from "@xyflow/react";
import { useReveal } from "../reveal/RevealContext";
import clsx from "clsx";

export function GraphEdge(props: EdgeProps) {
  const {
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data,
  } = props;

  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const { phase } = useReveal();
  const PHASE_ORDER = ["pending", "overlay", "dim", "evidence", "edges", "camera", "root_cause", "summary", "timeline", "complete"];
  const currentPhaseIdx = PHASE_ORDER.indexOf(phase);
  
  const isEdgesPhaseActive = currentPhaseIdx >= PHASE_ORDER.indexOf("edges");
  const isDimmedPhase = currentPhaseIdx >= PHASE_ORDER.indexOf("dim");
  const isEvidencePath = Boolean(data && (data as { isEvidencePath?: boolean }).isEvidencePath);
  const showAsEvidence = isEvidencePath && isEdgesPhaseActive;
  
  const edgeColor = showAsEvidence ? "#F59E0B" : isDimmedPhase ? "rgba(0,0,0,0.1)" : "#CBD5E1";
  const edgeWidth = showAsEvidence ? 3 : 1.5;

  return (
    <BaseEdge 
      path={edgePath} 
      markerEnd={markerEnd} 
      style={{
        ...style,
        stroke: edgeColor,
        strokeWidth: edgeWidth,
        transition: "all 0.3s ease",
      }} 
      className={clsx(showAsEvidence && "react-flow__edge-path--animating")}
    />
  );
}
