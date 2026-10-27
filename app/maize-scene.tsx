"use client";

import { type ThreeElements, Canvas, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import {
  Component,
  createElement,
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import * as THREE from "three";
import { FallbackIllustration } from "./maize-scene-illustration";

// React Three Fiber intrinsic elements belong to the Three.js renderer.
function ThreeGroup(props: Readonly<ThreeElements["group"]>) {
  return createElement("group", props);
}
function ThreeMesh(props: Readonly<ThreeElements["mesh"]>) {
  return createElement("mesh", props);
}
function ThreeShapeGeometry(props: Readonly<ThreeElements["shapeGeometry"]>) {
  return createElement("shapeGeometry", props);
}
function ThreeMeshStandardMaterial(
  props: Readonly<ThreeElements["meshStandardMaterial"]>,
) {
  return createElement("meshStandardMaterial", props);
}
function ThreeCylinderGeometry(
  props: Readonly<ThreeElements["cylinderGeometry"]>,
) {
  return createElement("cylinderGeometry", props);
}
function ThreeColor(props: Readonly<ThreeElements["color"]>) {
  return createElement("color", props);
}
function ThreeFog(props: Readonly<ThreeElements["fog"]>) {
  return createElement("fog", props);
}
function ThreeAmbientLight(props: Readonly<ThreeElements["ambientLight"]>) {
  return createElement("ambientLight", props);
}
function ThreeDirectionalLight(
  props: Readonly<ThreeElements["directionalLight"]>,
) {
  return createElement("directionalLight", props);
}
function ThreeBoxGeometry(props: Readonly<ThreeElements["boxGeometry"]>) {
  return createElement("boxGeometry", props);
}

function ThreeConeGeometry(props: Readonly<ThreeElements["coneGeometry"]>) {
  return createElement("coneGeometry", props);
}

function ThreePointLight(props: Readonly<ThreeElements["pointLight"]>) {
  return createElement("pointLight", props);
}

function ThreeTubeGeometry(props: Readonly<ThreeElements["tubeGeometry"]>) {
  return createElement("tubeGeometry", props);
}

function ThreeMeshBasicMaterial(
  props: Readonly<ThreeElements["meshBasicMaterial"]>,
) {
  return createElement("meshBasicMaterial", props);
}

function RenderOnVisibility() {
  const setFrameloop = useThree((state) => state.setFrameloop);
  const canvas = useThree((state) => state.gl.domElement);

  useEffect(() => {
    let frame = 0;
    const observer = new IntersectionObserver(([entry]) => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => {
        setFrameloop(entry.isIntersecting ? "always" : "never");
      });
    });
    observer.observe(canvas);
    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [canvas, setFrameloop]);

  return null;
}

type MaizeSceneProps = {
  reducedMotion: boolean;
};

type BoundaryProps = {
  children: ReactNode;
  fallback: ReactNode;
};

type BoundaryState = {
  failed: boolean;
};

type SceneContentsProps = {
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
};

class SceneErrorBoundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { failed: false };

  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  componentDidCatch(): void {
    // A static illustration is always available if WebGL or a GPU resource fails.
  }

  render(): ReactNode {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

function Leaf({
  angle,
  azimuth,
  height,
  length,
  tone,
}: Readonly<{
  angle: number;
  azimuth: number;
  height: number;
  length: number;
  tone: string;
}>) {
  const group = useRef<THREE.Group>(null);
  const shape = useMemo(() => {
    const form = new THREE.Shape();
    form.moveTo(0, 0);
    form.quadraticCurveTo(
      length * 0.2,
      length * 0.2,
      length * 0.53,
      length * 0.13,
    );
    form.quadraticCurveTo(length * 0.84, length * 0.07, length, 0);
    form.quadraticCurveTo(length * 0.5, -length * 0.035, 0, 0);
    return form;
  }, [length]);

  return (
    <ThreeGroup
      ref={group}
      position={[0, height, 0]}
      rotation={[0, azimuth, angle]}
    >
      <ThreeMesh position={[0, 0, 0]} castShadow>
        <ThreeShapeGeometry args={[shape, 16]} />
        <ThreeMeshStandardMaterial
          color={tone}
          roughness={0.62}
          side={THREE.DoubleSide}
        />
      </ThreeMesh>
      <ThreeMesh
        position={[length * 0.48, length * 0.055, 0.012]}
        rotation={[0, 0, Math.PI / 2]}
      >
        <ThreeCylinderGeometry args={[0.006, 0.012, length * 0.88, 6]} />
        <ThreeMeshStandardMaterial color="#d4dea1" roughness={0.8} />
      </ThreeMesh>
    </ThreeGroup>
  );
}

function Root({ angle, length }: Readonly<{ angle: number; length: number }>) {
  const curve = useMemo(() => {
    const points = [
      new THREE.Vector3(0, 0.1, 0),
      new THREE.Vector3(Math.sin(angle) * 0.09, -length * 0.36, 0.015),
      new THREE.Vector3(Math.sin(angle) * length * 0.54, -length * 0.78, 0.035),
      new THREE.Vector3(Math.sin(angle) * length, -length, 0.055),
    ];
    return new THREE.CatmullRomCurve3(points);
  }, [angle, length]);

  return (
    <ThreeMesh>
      <ThreeTubeGeometry args={[curve, 16, 0.008, 5, false]} />
      <ThreeMeshStandardMaterial color="#c69b66" roughness={0.9} />
    </ThreeMesh>
  );
}

function MaizePlant() {
  const stalk = useRef<THREE.Group>(null);
  const leaves = [
    {
      angle: -0.86,
      azimuth: -0.12,
      height: 0.75,
      length: 0.87,
      tone: "#39844f",
      phase: 0.2,
    },
    {
      angle: 0.94,
      azimuth: 2.65,
      height: 0.93,
      length: 0.78,
      tone: "#63a85f",
      phase: 1.1,
    },
    {
      angle: -0.78,
      azimuth: 0.95,
      height: 1.15,
      length: 0.78,
      tone: "#518f4d",
      phase: 2.2,
    },
    {
      angle: 0.86,
      azimuth: 3.45,
      height: 1.33,
      length: 0.69,
      tone: "#78b56a",
      phase: 0.9,
    },
    {
      angle: -0.66,
      azimuth: -0.72,
      height: 1.53,
      length: 0.63,
      tone: "#68a55c",
      phase: 2.8,
    },
    {
      angle: 0.7,
      azimuth: 2.1,
      height: 1.7,
      length: 0.53,
      tone: "#8abb72",
      phase: 1.8,
    },
  ];

  return (
    <ThreeGroup ref={stalk} position={[0, -0.34, 0]}>
      <ThreeMesh position={[0, 0.98, 0]} castShadow>
        <ThreeCylinderGeometry args={[0.095, 0.14, 2, 18, 1]} />
        <ThreeMeshStandardMaterial color="#a1b960" roughness={0.7} />
      </ThreeMesh>
      <ThreeMesh position={[0.025, 1.01, 0.085]}>
        <ThreeCylinderGeometry args={[0.012, 0.02, 1.84, 7]} />
        <ThreeMeshStandardMaterial color="#d7d293" roughness={0.8} />
      </ThreeMesh>
      {leaves.map((leaf) => (
        <Leaf
          key={leaf.phase + leaf.angle}
          angle={leaf.angle}
          azimuth={leaf.azimuth}
          height={leaf.height}
          length={leaf.length}
          tone={leaf.tone}
        />
      ))}
      {Array.from({ length: 11 }, (_, index) => {
        const angle = (index / 11) * Math.PI * 2;
        const length = 0.78 + (index % 3) * 0.13;
        return <Root key={index} angle={angle} length={length} />;
      })}
      <ThreeMesh position={[0.12, 1.42, 0]} rotation={[0, 0, -0.2]}>
        <ThreeCylinderGeometry args={[0.085, 0.052, 0.68, 9]} />
        <ThreeMeshStandardMaterial color="#d6b555" roughness={0.78} />
      </ThreeMesh>
      <ThreeMesh position={[0.12, 1.42, 0]} rotation={[0, 0, -0.2]}>
        <ThreeConeGeometry args={[0.045, 0.43, 7]} />
        <ThreeMeshStandardMaterial color="#c9a754" roughness={0.76} />
      </ThreeMesh>
      <ThreeMesh position={[0.12, 1.64, 0]} rotation={[0, 0, -0.2]}>
        <ThreeConeGeometry args={[0.024, 0.2, 7]} />
        <ThreeMeshStandardMaterial color="#e0bd69" roughness={0.74} />
      </ThreeMesh>
    </ThreeGroup>
  );
}

function SceneContents({ controlsRef }: Readonly<SceneContentsProps>) {
  return (
    <>
      <ThreeColor attach="background" args={["#0b1718"]} />
      <ThreeFog attach="fog" args={["#0b1718", 4, 8]} />
      <ThreeAmbientLight intensity={1.8} />
      <ThreeDirectionalLight
        position={[3, 4, 4]}
        intensity={2.5}
        color="#e5ebc7"
      />
      <ThreePointLight position={[-2, 1, 2]} intensity={3} color="#7dcba2" />
      <ThreeGroup position={[0, 0.05, 0]} rotation={[0.08, -0.18, 0]}>
        <ThreeMesh position={[0, -0.34, 0]} receiveShadow>
          <ThreeBoxGeometry args={[2.3, 0.08, 1.5]} />
          <ThreeMeshStandardMaterial color="#6f664d" roughness={0.96} />
        </ThreeMesh>
        <ThreeMesh position={[0, -0.06, -0.73]}>
          <ThreeBoxGeometry args={[2.3, 0.6, 0.08]} />
          <ThreeMeshBasicMaterial color="#a0835e" wireframe />
        </ThreeMesh>
        <ThreeMesh position={[-1.12, -0.06, 0]}>
          <ThreeBoxGeometry args={[0.06, 0.6, 0.08]} />
          <ThreeMeshBasicMaterial color="#a0835e" wireframe />
        </ThreeMesh>
        <ThreeMesh position={[1.12, -0.06, 0]}>
          <ThreeBoxGeometry args={[0.06, 0.6, 0.08]} />
          <ThreeMeshBasicMaterial color="#a0835e" wireframe />
        </ThreeMesh>
        <ThreeMesh position={[0, -0.06, 0.73]} rotation={[0, Math.PI / 2, 0]}>
          <ThreeBoxGeometry args={[1.5, 0.6, 0.08]} />
          <ThreeMeshBasicMaterial color="#a0835e" wireframe />
        </ThreeMesh>
        <MaizePlant />
      </ThreeGroup>
      <OrbitControls
        ref={controlsRef}
        makeDefault
        enableDamping={false}
        dampingFactor={0.09}
        minDistance={3.2}
        maxDistance={6.2}
        minPolarAngle={0.5}
        maxPolarAngle={2.2}
        enablePan={false}
        autoRotate={false}
        regress
      />
      <RenderOnVisibility />
    </>
  );
}

export default function MaizeScene({
  reducedMotion,
}: Readonly<MaizeSceneProps>) {
  const [resetKey, setResetKey] = useState(0);
  const [webglAvailable, setWebglAvailable] = useState<boolean | null>(null);
  const controlsRef = useRef<OrbitControlsImpl>(null);

  const adjustView = (axis: "horizontal" | "vertical", direction: number) => {
    const controls = controlsRef.current;
    if (!controls) return;
    if (axis === "horizontal") {
      controls.setAzimuthalAngle(
        controls.getAzimuthalAngle() + direction * 0.18,
      );
    } else {
      controls.setPolarAngle(controls.getPolarAngle() + direction * 0.14);
    }
    controls.update();
  };

  const adjustZoom = (inward: boolean) => {
    const controls = controlsRef.current;
    if (!controls) return;
    if (inward) controls.dollyIn(1.18);
    else controls.dollyOut(1.18);
    controls.update();
  };

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      try {
        const canvas = document.createElement("canvas");
        const context =
          canvas.getContext("webgl2") || canvas.getContext("webgl");
        setWebglAvailable(Boolean(context));
        context?.getExtension("WEBGL_lose_context")?.loseContext();
      } catch {
        setWebglAvailable(false);
      }
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  return (
    <div className="scene-stage">
      {!reducedMotion && webglAvailable === true ? (
        <SceneErrorBoundary fallback={<FallbackIllustration />}>
          <div className="maize-scene" aria-hidden="true">
            <Canvas
              key={resetKey}
              shadows
              dpr={[1, 1.5]}
              frameloop="demand"
              camera={{ position: [3.4, 3, 5.3], fov: 39 }}
              gl={{
                antialias: true,
                alpha: false,
                powerPreference: "low-power",
              }}
            >
              <Suspense fallback={null}>
                <SceneContents controlsRef={controlsRef} />
              </Suspense>
            </Canvas>
          </div>
        </SceneErrorBoundary>
      ) : (
        <FallbackIllustration />
      )}
      <div className="scene-watermark" aria-hidden="true">
        SCHEMATIC · NOT MEASURED MORPHOLOGY
      </div>
      <fieldset
        className="scene-controls"

        aria-label="Maize illustration camera controls"
      >
        <span className="scene-hint">
          {reducedMotion || webglAvailable !== true
            ? "STATIC ILLUSTRATION"
            : "DRAG TO ORBIT · SCROLL TO ZOOM"}
        </span>
        {!reducedMotion && webglAvailable === true && (
          <>
            <button
              type="button"
              aria-label="Rotate camera left"
              onClick={() => adjustView("horizontal", -1)}
            >
              ←
            </button>
            <button
              type="button"
              aria-label="Rotate camera right"
              onClick={() => adjustView("horizontal", 1)}
            >
              →
            </button>
            <button
              type="button"
              aria-label="Tilt camera up"
              onClick={() => adjustView("vertical", -1)}
            >
              ↑
            </button>
            <button
              type="button"
              aria-label="Tilt camera down"
              onClick={() => adjustView("vertical", 1)}
            >
              ↓
            </button>
            <button
              type="button"
              aria-label="Zoom in"
              onClick={() => adjustZoom(true)}
            >
              +
            </button>
            <button
              type="button"
              aria-label="Zoom out"
              onClick={() => adjustZoom(false)}
            >
              −
            </button>
            <button type="button" onClick={() => setResetKey((key) => key + 1)}>
              Reset view
            </button>
          </>
        )}
      </fieldset>
    </div>
  );
}
