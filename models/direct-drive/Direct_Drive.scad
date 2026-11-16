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
        // One full-depth trim removes the hinge and latch, including the
        // slivers at their roots. The thread crests fit within r = 26.21.
        translate([0,0,-3]) cylinder(r=27.72,h=6.5,$fn=360);
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

// Rounded pads define a continuous tapered web. The high section stays
// on the lens side of the hub. The rail under the servo stays below its case.
module web_pad(x, y, z, radius) {
    translate([x,y,z]) cylinder(r=radius,h=0.25,$fn=48);
}

module ring_gusset() {
    difference() {
        hull() {
            for (angle = [-40,-25,-10,5,16]) {
                web_pad(27.1*cos(angle),27.1*sin(angle),0.25,2.35);
                web_pad(26.8*cos(angle),26.8*sin(angle),5.85,1.15);
            }
            web_pad(29.5,-15.9,0.25,2.25);
            web_pad(29.5,-15.9,5.85,1.15);
        }
        // Maintain the full aperture even where the arc pads meet.
        translate([0,0,0.15]) cylinder(r=rim_inner_radius,h=6.1);
    }
}

module rounded_mount_ear(x) {
    hull() {
        for (dx = [-1.55,1.55])
            translate([x+dx,mount_face_y,1.25])
                axial_cylinder(1.05,mount_plate_thickness);
        translate([x,mount_face_y,mount_hole_z])
            axial_cylinder(2.65,mount_plate_thickness);
    }
}

module cradle_foot(x, y) {
    translate([x,y,0.25]) cylinder(r=3.15,h=1.4,$fn=72);
}

module cradle_spine(x) {
    hull() {
        translate([x,mount_face_y,1.84])
            axial_cylinder(1.0,mount_plate_thickness);
        translate([x-1,mount_face_y,0.9])
            cube([2,mount_plate_thickness,0.3]);
    }
}

module mount() {
    hole_xs = [mount_center_x-mount_hole_spacing/2,
               mount_center_x+mount_hole_spacing/2];
    foot_y = mount_face_y + mount_plate_thickness - 3.15 - 0.2;
    difference() {
        union() {
            ring_gusset();

            // Keep the wide footing beneath the case. The retained spine
            // rises only on the shaft side of the servo mounting plane.
            hull() {
                for (x = hole_xs) {
                    cradle_foot(x,foot_y);
                    translate([x,mount_face_y+mount_plate_thickness/2,0.25])
                        cylinder(r=0.85,h=1.4,$fn=48);
                }
            }
            hull() {
                for (x = hole_xs) cradle_spine(x);
            }

            // Run both screw bosses into the rail over a gradual taper.
            // This gives the ears a broad root through the print layers.
            for (i = [0,1]) {
                x = hole_xs[i];
                slope_end = x + (hole_xs[1-i]-x)*0.40;
                hull() {
                    rounded_mount_ear(x);
                    cradle_spine(slope_end);
                }
            }
        }
        // Leave running clearance around the servo's output wheel.
        translate([pivot.x,mount_face_y-0.1,pivot.z])
            axial_cylinder(servo_wheel_radius+0.45,pivot.y-mount_face_y+0.2);
        // The flared footing can touch the bore when the tab spacing changes.
        translate([0,0,0.15]) cylinder(r=rim_inner_radius,h=11);
        for (x = hole_xs)
            translate([x,mount_face_y-0.25,mount_hole_z])
                axial_cylinder(mount_hole_diameter/2,mount_plate_thickness+0.5);
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
