from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable


Point = tuple[int, int] | None


@dataclass(frozen=True)
class Curve:
    name: str
    p: int
    a: int
    b: int
    generator: Point

    def f(self, x: int) -> int:
        return (x * x * x + self.a * x + self.b) % self.p


@dataclass(frozen=True)
class TransitionLedger:
    phase: int
    op: str
    point: Point
    next_point: Point
    D: int | None
    U: int | None
    V: int | None
    m: int | None
    eea_quotients: tuple[int, ...]
    lambda_value: int | None
    ell: int | None
    x_next: int | None
    L: int | None
    omega: int | None
    sign_L: str | None
    boundary: str | None = None

    def to_dict(self) -> dict[str, object]:
        row = asdict(self)
        row["point"] = point_to_json(self.point)
        row["next_point"] = point_to_json(self.next_point)
        return row

    def paper_row(self) -> dict[str, int | str | None]:
        return {
            "d": self.phase,
            "op": self.op,
            "D": self.D,
            "U": self.U,
            "V": self.V,
            "m": self.m,
            "lambda": self.lambda_value,
            "ell": self.ell,
            "x_next": self.x_next,
            "L": self.L,
            "omega": self.omega,
        }


def toy_curve_97() -> Curve:
    return Curve(
        name="toy_E97_y2_x3_plus_7_G_96_54",
        p=97,
        a=0,
        b=7,
        generator=(96, 54),
    )


def point_to_json(point: Point) -> list[int] | None:
    if point is None:
        return None
    return [point[0], point[1]]


def point_key(point: Point) -> tuple[str, int, int] | tuple[str]:
    if point is None:
        return ("inf",)
    return ("point", point[0], point[1])


def point_x_key(point: Point) -> tuple[str, int] | tuple[str]:
    if point is None:
        return ("inf",)
    return ("x", point[0])


def inv_mod(value: int, modulus: int) -> int:
    return pow(value % modulus, -1, modulus)


def eea_quotients(denominator: int, modulus: int) -> tuple[int, ...]:
    a = modulus
    b = denominator % modulus
    if b == 0:
        raise ValueError("zero denominator has no EEA quotient trace")

    quotients: list[int] = []
    while b:
        q, r = divmod(a, b)
        quotients.append(q)
        a, b = b, r
    if a != 1:
        raise ValueError("denominator is not invertible")
    return tuple(quotients)


def on_curve(curve: Curve, point: Point) -> bool:
    if point is None:
        return True
    x, y = point
    return (y * y - (x * x * x + curve.a * x + curve.b)) % curve.p == 0


def negate(curve: Curve, point: Point) -> Point:
    if point is None:
        return None
    x, y = point
    return (x, (-y) % curve.p)


def add(curve: Curve, left: Point, right: Point) -> Point:
    if left is None:
        return right
    if right is None:
        return left

    p = curve.p
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % p == 0:
        return None

    if left == right:
        denominator = (2 * y1) % p
        numerator = (3 * x1 * x1 + curve.a) % p
    else:
        denominator = (x2 - x1) % p
        numerator = (y2 - y1) % p

    slope = (numerator * inv_mod(denominator, p)) % p
    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    return (x3, y3)


def mul(curve: Curve, scalar: int, point: Point | None = None) -> Point:
    addend = curve.generator if point is None else point
    result: Point = None
    k = scalar
    while k:
        if k & 1:
            result = add(curve, result, addend)
        addend = add(curve, addend, addend)
        k >>= 1
    return result


def orbit(curve: Curve) -> list[Point]:
    if curve.generator is None:
        raise ValueError("generator cannot be point at infinity")
    if not on_curve(curve, curve.generator):
        raise ValueError("generator is not on curve")

    points: list[Point] = [None]
    seen: set[Point] = {None}
    point: Point = None
    while True:
        point = add(curve, point, curve.generator)
        if point is None:
            break
        if point in seen:
            raise RuntimeError("generator orbit repeated before returning to infinity")
        points.append(point)
        seen.add(point)
    return points


def sign(value: int) -> str:
    if value < 0:
        return "negative"
    if value > 0:
        return "positive"
    return "zero"


def transition_ledger_for_points(
    curve: Curve,
    phase: int,
    point: Point,
    next_point: Point,
    order: int | None = None,
) -> TransitionLedger:
    generator = curve.generator
    if generator is None:
        raise ValueError("generator cannot be infinity")

    if point is None:
        return TransitionLedger(
            phase=phase,
            op="identity",
            point=point,
            next_point=next_point,
            D=None,
            U=None,
            V=None,
            m=None,
            eea_quotients=(),
            lambda_value=None,
            ell=None,
            x_next=next_point[0] if next_point else None,
            L=None,
            omega=None,
            sign_L=None,
            boundary="identity-to-generator",
        )

    x, y = point
    xg, yg = generator
    p = curve.p

    if phase == 1:
        op = "dbl"
        denominator = (2 * y) % p
        numerator = (3 * x * x + curve.a) % p
        raw_x = None
        if denominator:
            v = inv_mod(denominator, p)
            lambda_value = (numerator * v) % p
            raw_x = lambda_value * lambda_value - 2 * x
    elif x == xg and (y + yg) % p == 0:
        return TransitionLedger(
            phase=phase,
            op="+G_boundary",
            point=point,
            next_point=next_point,
            D=0,
            U=(yg - y) % p,
            V=None,
            m=None,
            eea_quotients=(),
            lambda_value=None,
            ell=None,
            x_next=None,
            L=None,
            omega=None,
            sign_L=None,
            boundary="P_d_plus_G_is_infinity",
        )
    else:
        op = "+G"
        denominator = (xg - x) % p
        numerator = (yg - y) % p
        raw_x = None
        if denominator:
            v = inv_mod(denominator, p)
            lambda_value = (numerator * v) % p
            raw_x = lambda_value * lambda_value - x - xg

    if denominator == 0 or raw_x is None:
        return TransitionLedger(
            phase=phase,
            op=f"{op}_boundary",
            point=point,
            next_point=next_point,
            D=denominator,
            U=numerator,
            V=None,
            m=None,
            eea_quotients=(),
            lambda_value=None,
            ell=None,
            x_next=next_point[0] if next_point else None,
            L=None,
            omega=None,
            sign_L=None,
            boundary="zero-denominator",
        )

    x_next = next_point[0] if next_point is not None else None
    if x_next is None:
        return TransitionLedger(
            phase=phase,
            op=f"{op}_boundary",
            point=point,
            next_point=next_point,
            D=denominator,
            U=numerator,
            V=v,
            m=(denominator * v - 1) // p,
            eea_quotients=eea_quotients(denominator, p),
            lambda_value=lambda_value,
            ell=(numerator * v - lambda_value) // p,
            x_next=None,
            L=None,
            omega=math.gcd(denominator * v, numerator * v),
            sign_L=None,
            boundary="next-point-infinity",
        )

    residue = raw_x % p
    if residue != x_next:
        raise RuntimeError(
            f"ledger x mismatch at phase {phase}: formula {residue}, orbit {x_next}"
        )

    lift_l = (raw_x - x_next) // p
    return TransitionLedger(
        phase=phase,
        op=op,
        point=point,
        next_point=next_point,
        D=denominator,
        U=numerator,
        V=v,
        m=(denominator * v - 1) // p,
        eea_quotients=eea_quotients(denominator, p),
        lambda_value=lambda_value,
        ell=(numerator * v - lambda_value) // p,
        x_next=x_next,
        L=lift_l,
        omega=math.gcd(denominator * v, numerator * v),
        sign_L=sign(lift_l),
    )


def transition_ledger(curve: Curve, points: list[Point], phase: int) -> TransitionLedger:
    n = len(points)
    return transition_ledger_for_points(
        curve=curve,
        phase=phase,
        point=points[phase % n],
        next_point=points[(phase + 1) % n],
        order=n,
    )


def transition_ledgers(curve: Curve, points: Iterable[Point]) -> list[TransitionLedger]:
    orbit_points = list(points)
    return [transition_ledger(curve, orbit_points, phase) for phase in range(len(orbit_points))]
