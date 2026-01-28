"""
Standalone simulation for a RoboCup-style run:
- Follow line with omni strafing
- React to green markers
- Enter zone, pick balls, drop to green/red
No external dependencies beyond tkinter (optional for visuals).
"""

from __future__ import annotations

import math
import time

try:
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def norm(v: tuple[float, float]) -> float:
    return math.hypot(v[0], v[1])


def normalize(v: tuple[float, float]) -> tuple[float, float]:
    n = norm(v)
    if n == 0:
        return (0.0, 0.0)
    return (v[0] / n, v[1] / n)


def rotate(v: tuple[float, float], angle: float) -> tuple[float, float]:
    ca = math.cos(angle)
    sa = math.sin(angle)
    return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)


def wrap_angle(rad: float) -> float:
    while rad > math.pi:
        rad -= 2 * math.pi
    while rad < -math.pi:
        rad += 2 * math.pi
    return rad


def nearest_point_on_segment(
    p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]
) -> tuple[tuple[float, float], float]:
    ab = (b[0] - a[0], b[1] - a[1])
    ap = (p[0] - a[0], p[1] - a[1])
    ab2 = dot(ab, ab)
    if ab2 == 0:
        return a, 0.0
    t = clamp(dot(ap, ab) / ab2, 0.0, 1.0)
    q = (a[0] + ab[0] * t, a[1] + ab[1] * t)
    return q, t


def nearest_point_on_polyline(
    p: tuple[float, float], pts: list[tuple[float, float]]
) -> tuple[tuple[float, float], tuple[float, float], int, float, float]:
    best = None
    best_d = 1e9
    best_dir = (1.0, 0.0)
    best_idx = 0
    best_t = 0.0
    for i in range(len(pts) - 1):
        q, t = nearest_point_on_segment(p, pts[i], pts[i + 1])
        d = dist(p, q)
        if d < best_d:
            best_d = d
            best = q
            best_idx = i
            best_t = t
            best_dir = normalize((pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
    return best, best_dir, best_idx, best_t, best_d


class Marker:
    def __init__(self, pos: tuple[float, float], command: str):
        self.pos = pos
        self.command = command  # "left" or "right"
        self.used = False


class Ball:
    def __init__(self, pos: tuple[float, float], kind: str):
        self.pos = pos
        self.kind = kind  # "alive" or "dead"


class Environment:
    def __init__(self):
        self.width = 520
        self.height = 360

        # Line path with a few turns
        self.line_path = [
            (60, 320),
            (60, 220),
            (180, 220),
            (180, 140),
            (320, 140),
            (420, 80),
        ]

        self.markers = [
            Marker((55, 260), "right"),
            Marker((150, 215), "left"),
        ]

        # Zone area near the end of the line
        self.zone_rect = (360, 40, 500, 200)  # x1, y1, x2, y2
        self.zone_center = (430, 120)

        self.drop_green = (370, 50, 410, 90)
        self.drop_red = (450, 150, 490, 190)

        self.exit_point = (320, 240)

        self.balls = [
            Ball((420, 80), "alive"),
            Ball((460, 120), "dead"),
            Ball((410, 160), "alive"),
        ]


class Robot:
    def __init__(self):
        self.pos = [60.0, 340.0]
        self.heading = -math.pi / 2  # facing up
        self.mode = "line"
        self.zone_state = "search"
        self.carrying = None
        self.alive_count = 0
        self.dead_count = 0

        self.marker_timer = 0.0
        self.marker_bias = 0.0

        self.turn_timer = 0.0
        self.back_timer = 0.0
        self.target_ball = None

        self.last_log = ""

    def log(self, msg: str) -> None:
        if msg != self.last_log:
            print(msg)
            self.last_log = msg

    def _apply_motion(self, vx: float, vy: float, omega: float, dt: float) -> None:
        self.pos[0] += vx * dt
        self.pos[1] += vy * dt
        self.heading = wrap_angle(self.heading + omega * dt)

    def step(self, env: Environment, dt: float) -> None:
        if self.mode == "line":
            self._step_line(env, dt)
        elif self.mode == "zone":
            self._step_zone(env, dt)
        elif self.mode == "done":
            self.log("Done: run completed")

    def _step_line(self, env: Environment, dt: float) -> None:
        # Trigger marker bias if close
        for m in env.markers:
            if not m.used and dist(tuple(self.pos), m.pos) < 18:
                m.used = True
                self.marker_timer = 1.0
                self.marker_bias = -1.0 if m.command == "left" else 1.0
                self.log(f"Line: green marker {m.command}")

        if self.marker_timer > 0:
            self.marker_timer -= dt
        else:
            self.marker_bias = 0.0

        nearest, tangent, seg_idx, seg_t, seg_d = nearest_point_on_polyline(tuple(self.pos), env.line_path)
        normal = (-tangent[1], tangent[0])
        err = dot((self.pos[0] - nearest[0], self.pos[1] - nearest[1]), normal)

        # Omni line follow: forward along tangent + strafe to center
        line_speed = 70.0
        k_lat = 2.0
        v_t = line_speed
        v_n = -k_lat * err
        vx = v_t * tangent[0] + v_n * normal[0]
        vy = v_t * tangent[1] + v_n * normal[1]

        heading_target = math.atan2(tangent[1], tangent[0]) + self.marker_bias * math.radians(40)
        omega = clamp(wrap_angle(heading_target - self.heading) * 2.2, -3.0, 3.0)

        self._apply_motion(vx, vy, omega, dt)

        # Switch to zone at end of line
        if dist(tuple(self.pos), env.line_path[-1]) < 20:
            self.mode = "zone"
            self.zone_state = "search"
            self.log("Switch: line -> zone")

    def _step_zone(self, env: Environment, dt: float) -> None:
        if self.zone_state == "search":
            # Find nearest visible ball
            fov = math.radians(70)
            max_range = 140
            best = None
            best_d = 1e9
            for b in env.balls:
                to_b = (b.pos[0] - self.pos[0], b.pos[1] - self.pos[1])
                d = norm(to_b)
                if d > max_range:
                    continue
                ang = wrap_angle(math.atan2(to_b[1], to_b[0]) - self.heading)
                if abs(ang) < fov / 2 and d < best_d:
                    best = b
                    best_d = d
            if best:
                self.target_ball = best
                self.zone_state = "approach"
                self.log(f"Zone: target {best.kind} ball")
            else:
                # Roam toward zone center
                self._go_to_point(env.zone_center, dt, speed=50.0)

        elif self.zone_state == "approach":
            if self.target_ball not in env.balls:
                self.zone_state = "search"
                return
            b = self.target_ball
            to_b = (b.pos[0] - self.pos[0], b.pos[1] - self.pos[1])
            d = norm(to_b)
            ang = wrap_angle(math.atan2(to_b[1], to_b[0]) - self.heading)
            error_x = math.sin(ang)

            # Strafe + forward (omni)
            vx_body = clamp(140.0 * error_x, -60.0, 60.0)  # right is +x
            vy_body = 60.0
            vx, vy = rotate((vx_body, vy_body), self.heading)
            omega = clamp(ang * 1.5, -2.5, 2.5)
            self._apply_motion(vx, vy, omega, dt)

            if d < 18 and abs(error_x) < 0.15:
                self.carrying = b.kind
                env.balls.remove(b)
                self.target_ball = None
                self.zone_state = "go_drop"
                self.log(f"Zone: picked {self.carrying}")

        elif self.zone_state == "go_drop":
            target = self._drop_center(env)
            arrived = self._go_to_point(target, dt, speed=70.0)
            if arrived:
                self.zone_state = "dump_prep"
                self.turn_timer = 0.8
                self.log("Zone: dump prep (turn 180)")

        elif self.zone_state == "dump_prep":
            # Turn around
            self.turn_timer -= dt
            omega = clamp(math.pi * 1.2, -5.0, 5.0)
            self._apply_motion(0.0, 0.0, omega, dt)
            if self.turn_timer <= 0:
                self.zone_state = "dump_back"
                self.back_timer = 1.2
                self.log("Zone: backing to dump")

        elif self.zone_state == "dump_back":
            self.back_timer -= dt
            # Move backward in body frame
            vx, vy = rotate((0.0, -60.0), self.heading)
            self._apply_motion(vx, vy, 0.0, dt)
            if self.back_timer <= 0:
                if self.carrying == "alive":
                    self.alive_count += 1
                else:
                    self.dead_count += 1
                self.carrying = None
                self.zone_state = "exit" if not env.balls else "search"
                self.log("Zone: dumped")

        elif self.zone_state == "exit":
            arrived = self._go_to_point(env.exit_point, dt, speed=70.0)
            if arrived:
                self.mode = "done"
                self.log("Zone: exit -> done")

    def _drop_center(self, env: Environment) -> tuple[float, float]:
        if self.carrying == "alive":
            x1, y1, x2, y2 = env.drop_green
        else:
            x1, y1, x2, y2 = env.drop_red
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def _go_to_point(self, target: tuple[float, float], dt: float, speed: float) -> bool:
        to_t = (target[0] - self.pos[0], target[1] - self.pos[1])
        d = norm(to_t)
        if d < 8:
            return True
        dir_v = normalize(to_t)
        vx = dir_v[0] * speed
        vy = dir_v[1] * speed
        heading_target = math.atan2(dir_v[1], dir_v[0])
        omega = clamp(wrap_angle(heading_target - self.heading) * 2.0, -3.0, 3.0)
        self._apply_motion(vx, vy, omega, dt)
        return False


class SimulationUI:
    def __init__(self, env: Environment, robot: Robot):
        self.env = env
        self.robot = robot
        self.scale = 1.5
        self.root = tk.Tk()
        self.root.title("Standalone Simulation (mine)")
        self.canvas = tk.Canvas(self.root, width=int(env.width * self.scale), height=int(env.height * self.scale), bg="#f6f3ee")
        self.canvas.pack()
        self.info = tk.StringVar()
        self.label = tk.Label(self.root, textvariable=self.info, anchor="w", justify="left")
        self.label.pack(fill="x")
        self.last_time = time.time()
        self._tick()

    def _to_canvas(self, p: tuple[float, float]) -> tuple[float, float]:
        return (p[0] * self.scale, p[1] * self.scale)

    def _draw_robot(self) -> None:
        x, y = self.robot.pos
        heading = self.robot.heading
        size = 10
        p1 = (x + math.cos(heading) * size, y + math.sin(heading) * size)
        p2 = (x + math.cos(heading + 2.6) * size, y + math.sin(heading + 2.6) * size)
        p3 = (x + math.cos(heading - 2.6) * size, y + math.sin(heading - 2.6) * size)
        c1 = self._to_canvas(p1)
        c2 = self._to_canvas(p2)
        c3 = self._to_canvas(p3)
        self.canvas.create_polygon(c1, c2, c3, fill="#3b82f6", outline="#1e3a8a")

    def _draw(self) -> None:
        self.canvas.delete("all")

        # Line path
        pts = []
        for p in self.env.line_path:
            pts.extend(self._to_canvas(p))
        self.canvas.create_line(*pts, fill="#111111", width=6)

        # Markers
        for m in self.env.markers:
            cx, cy = self._to_canvas(m.pos)
            r = 8 * self.scale / 1.5
            self.canvas.create_rectangle(cx - r, cy - r, cx + r, cy + r, fill="#22c55e", outline="")
            self.canvas.create_text(cx, cy, text="L" if m.command == "left" else "R", fill="#0f172a")

        # Zone + drop
        zx1, zy1, zx2, zy2 = self.env.zone_rect
        x1, y1 = self._to_canvas((zx1, zy1))
        x2, y2 = self._to_canvas((zx2, zy2))
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#64748b", width=2)
        gx1, gy1, gx2, gy2 = self.env.drop_green
        self.canvas.create_rectangle(*self._to_canvas((gx1, gy1)), *self._to_canvas((gx2, gy2)), fill="#86efac", outline="")
        rx1, ry1, rx2, ry2 = self.env.drop_red
        self.canvas.create_rectangle(*self._to_canvas((rx1, ry1)), *self._to_canvas((rx2, ry2)), fill="#fca5a5", outline="")

        # Balls
        for b in self.env.balls:
            cx, cy = self._to_canvas(b.pos)
            r = 6
            color = "#22c55e" if b.kind == "alive" else "#111111"
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

        # Robot
        self._draw_robot()

        # Info
        self.info.set(
            f"mode={self.robot.mode}  zone={self.robot.zone_state}  carry={self.robot.carrying}  "
            f"alive={self.robot.alive_count} dead={self.robot.dead_count}"
        )

    def _tick(self) -> None:
        now = time.time()
        dt = clamp(now - self.last_time, 0.01, 0.05)
        self.last_time = now
        self.robot.step(self.env, dt)
        self._draw()
        self.root.after(33, self._tick)


def run_headless() -> None:
    env = Environment()
    robot = Robot()
    t0 = time.time()
    last = t0
    while time.time() - t0 < 40:
        now = time.time()
        dt = clamp(now - last, 0.01, 0.05)
        last = now
        robot.step(env, dt)
        time.sleep(0.03)


def main() -> None:
    env = Environment()
    robot = Robot()
    if tk is None:
        print("Tkinter not available, running headless simulation.")
        run_headless()
    else:
        SimulationUI(env, robot).root.mainloop()


if __name__ == "__main__":
    main()
