// Canon RF 35 mm direct drive cap. Dimensions in mm.
// Choose assembly, sweep, base, or cap. F6 renders the chosen part.
part = "assembly";
open_angle = 135;
display_angle = 0;

// Servo fit estimates. Confirm these against the actual SER0049 before export.
servo_body_length = 23;
servo_body_width = 12.2;
servo_body_depth = 20;
mount_hole_spacing = 28;
mount_hole_diameter = 2.3;
shaft_from_body_end = 6;
mount_hole_z_offset = 0;

// Smooth friction hub. Replace all four placeholders before print export.
shaft_recess_diameter = 5.4;
shaft_recess_depth = 1.8;
screw_clearance_diameter = 2.2;
screw_seat_thickness = 1.8;

$fn = 120;
ring_radius = 27.7;
rim_height = 6.75;
rim_inner_radius = 25.7;
lid_radius = 28.2;
lid_thickness = 1.6;
pivot = [38, -14, 8];
mount_face_y = -16.4;
mount_center_x = pivot.x + servo_body_length/2 - shaft_from_body_end;
mount_hole_z = pivot.z + mount_hole_z_offset;
mount_plate_thickness = 1.9;
servo_wheel_radius = 4.4;
hub_radius = 4.8;

// Original lens-facing geometry is at z <= 0 after this rigid transform.
module original_interface() {
    intersection() {
        rotate([90, 0, 0])
            translate([-39.28856, -29.816093, -27.976998])
                import("52mm_Lens_Cap-Base.STL", convexity=12);
        union() {
            translate([-100, -100, -10]) cube([200, 200, 10.001]);
            translate([0, 0, -0.001]) cylinder(r=27.74, h=3.01);
        }
    }
}

module axial_cylinder(radius, length) {
    rotate([-90,0,0]) cylinder(r=radius, h=length);
}

module rim() {
    difference() {
        translate([0,0,2.4]) cylinder(r=ring_radius, h=rim_height-2.4);
        translate([0,0,2.3]) cylinder(r=rim_inner_radius, h=rim_height-2.2);
    }
}

module mount() {
    hole_xs = [mount_center_x-mount_hole_spacing/2,
               mount_center_x+mount_hole_spacing/2];
    difference() {
        union() {
            // A low rail sits behind the servo case, with a gusset into the ring.
            hull() {
                translate([22,-17.5,0.20]) cube([4,4,3.3]);
                translate([hole_xs[0]-3,mount_face_y,0.20])
                    cube([6,mount_plate_thickness,3.2]);
            }
            translate([hole_xs[0]-3,mount_face_y,0.20])
                cube([mount_hole_spacing+6,mount_plate_thickness,1.35]);
            for (x = hole_xs)
                translate([x-3,mount_face_y,0.20])
                    cube([6,mount_plate_thickness,mount_hole_z+2.6-0.20]);
        }
        for (x = hole_xs)
            translate([x,mount_face_y-0.1,mount_hole_z])
                axial_cylinder(mount_hole_diameter/2,mount_plate_thickness+0.2);
    }
}

module base() {
    union() {
        original_interface();
        rim();
        mount();
    }
}

module lid_closed() {
    total_depth = shaft_recess_depth + screw_seat_thickness;
    difference() {
        union() {
            translate([0,0,pivot.z]) cylinder(r=lid_radius,h=lid_thickness);
            hull() {
                translate([23.5,-10,pivot.z]) cube([2.0,4,lid_thickness]);
                translate([pivot.x-1.9,pivot.y+0.4,pivot.z])
                    cube([1.9,2.8,lid_thickness]);
            }
            translate(pivot) axial_cylinder(hub_radius,total_depth);
        }
        translate(pivot+[0,-0.10,0])
            axial_cylinder(shaft_recess_diameter/2,shaft_recess_depth+0.10);
        translate(pivot+[0,-0.10,0])
            axial_cylinder(screw_clearance_diameter/2,total_depth+0.20);
    }
}

module lid(angle) {
    translate(pivot) rotate([0,angle,0]) translate(-pivot) lid_closed();
}

module servo_envelope() {
    translate([mount_center_x-servo_body_length/2,
               mount_face_y-servo_body_depth, pivot.z-servo_body_width/2])
        cube([servo_body_length,servo_body_depth,servo_body_width]);
    translate([pivot.x,mount_face_y,pivot.z])
        axial_cylinder(servo_wheel_radius,pivot.y-mount_face_y);
}

if (part == "base") base();
if (part == "cap") lid_closed();
if (part == "assembly" || part == "sweep") {
    color("#395d74") base();
    color("#555a63") servo_envelope();
    color("#c67330") lid(display_angle);
    if (part == "sweep")
        for (angle = [45,90,open_angle])
            color("#c67330",0.28) lid(angle);
}
