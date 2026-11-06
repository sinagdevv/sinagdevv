'use client';

import { OrbitControls, Sparkles } from '@react-three/drei';
import { Canvas, useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';

type SolarSceneProps = {
  paused: boolean;
  reducedMotion: boolean;
  activeProject: number;
  onProjectSelect: (index: number) => void;
};

const vertexShader = `varying vec2 vUv; varying vec3 vNormal; void main(){vUv=uv;vNormal=normal;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`;
const fragmentShader = `uniform float uTime; varying vec2 vUv; varying vec3 vNormal; void main(){float wave=sin(vUv.y*28.0+uTime*0.22)+sin(vUv.x*19.0-uTime*0.16);float grain=sin((vUv.x+vUv.y)*80.0+uTime*0.1);vec3 deep=vec3(0.55,0.16,0.025);vec3 hot=vec3(1.0,0.62,0.12);float light=0.48+0.22*wave+0.08*grain+0.28*max(dot(normalize(vNormal),vec3(0.35,0.65,1.0)),0.0);gl_FragColor=vec4(mix(deep,hot,clamp(light,0.0,1.0)),1.0);}`;

function Core({ paused, reducedMotion }: Pick<SolarSceneProps, 'paused' | 'reducedMotion'>) {
  const group = useRef<THREE.Group>(null);
  const material = useRef<THREE.ShaderMaterial>(null);
  useFrame((_, delta) => {
    if (paused || reducedMotion) return;
    if (group.current) group.current.rotation.y += delta * 0.055;
    if (material.current) material.current.uniforms.uTime.value += delta;
  });
  return <group ref={group}>
    <mesh>
      <sphereGeometry args={[1.28, 96, 96]} />
      <shaderMaterial ref={material} vertexShader={vertexShader} fragmentShader={fragmentShader} uniforms={{ uTime: { value: 0 } }} />
    </mesh>
    <mesh scale={1.055}>
      <sphereGeometry args={[1.28, 64, 64]} />
      <meshBasicMaterial color="#ffbf47" transparent opacity={0.075} blending={THREE.AdditiveBlending} depthWrite={false} />
    </mesh>
  </group>;
}

function Orbit({ radius, tilt, active, onClick }: { radius: number; tilt: number; active: boolean; onClick: () => void }) {
  const points = useMemo(() => Array.from({ length: 128 }, (_, index) => {
    const angle = (index / 128) * Math.PI * 2;
    return new THREE.Vector3(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
  }), [radius]);
  return <group rotation={[tilt, 0.2, tilt / 3]}>
    <line>
      <bufferGeometry><bufferAttribute attach="attributes-position" args={[new Float32Array(points.flatMap((point) => point.toArray())), 3]} count={points.length} /></bufferGeometry>
      <lineBasicMaterial color="#d6a443" transparent opacity={active ? 0.5 : 0.2} />
    </line>
    <mesh position={[radius, 0, 0]} onClick={onClick} onPointerOver={(event) => { event.stopPropagation(); document.body.style.cursor = 'pointer'; }} onPointerOut={() => { document.body.style.cursor = 'auto'; }}>
      <sphereGeometry args={[active ? 0.11 : 0.075, 20, 20]} />
      <meshBasicMaterial color={active ? '#ffe6a0' : '#d6a443'} />
    </mesh>
  </group>;
}

function SceneContents({ paused, reducedMotion, activeProject, onProjectSelect }: SolarSceneProps) {
  const rig = useRef<THREE.Group>(null);
  useFrame(({ pointer }) => {
    if (!rig.current || paused || reducedMotion) return;
    rig.current.rotation.x = THREE.MathUtils.lerp(rig.current.rotation.x, pointer.y * 0.08, 0.04);
    rig.current.rotation.z = THREE.MathUtils.lerp(rig.current.rotation.z, -pointer.x * 0.08, 0.04);
  });
  return <group ref={rig}>
    <Core paused={paused} reducedMotion={reducedMotion} />
    <Orbit radius={1.75} tilt={0.35} active={activeProject === 0} onClick={() => onProjectSelect(0)} />
    <Orbit radius={2.18} tilt={-0.42} active={activeProject === 1} onClick={() => onProjectSelect(1)} />
    <Orbit radius={2.55} tilt={0.12} active={activeProject === 2} onClick={() => onProjectSelect(2)} />
    <mesh rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[1.58, 0.008, 8, 128]} />
      <meshBasicMaterial color="#ffe6a0" transparent opacity={0.32} />
    </mesh>
    <Sparkles count={24} scale={5} size={1.5} speed={paused || reducedMotion ? 0 : 0.18} color="#ffe6a0" />
  </group>;
}

export function SolarScene(props: SolarSceneProps) {
  const [webgl, setWebgl] = useState<boolean | null>(null);
  useEffect(() => {
    const check = window.setTimeout(() => setWebgl(Boolean(document.createElement('canvas').getContext('webgl'))), 0);
    return () => window.clearTimeout(check);
  }, []);
  if (webgl === false) return <div className="scene-fallback" role="img" aria-label="Static solar core fallback"><span>SINAG</span><small>WEBGL FALLBACK / ORBITAL SYSTEM READY</small></div>;
  return <div className="solar-canvas" aria-label="Interactive SINAG solar core. Drag to inspect the core; use the project controls beside it for keyboard access.">
    {webgl === null ? <div className="scene-fallback" aria-hidden="true"><span>SINAG</span></div> : <Canvas camera={{ position: [0, 0.2, 5.1], fov: 36 }} dpr={[1, 1.6]} gl={{ antialias: true, alpha: true }}>
      <ambientLight intensity={0.12} />
      <pointLight position={[2, 2, 3]} color="#ffbf47" intensity={4} distance={8} />
      <SceneContents {...props} />
      <OrbitControls enablePan={false} enableZoom={false} rotateSpeed={0.42} autoRotate={false} />
    </Canvas>}
  </div>;
}
