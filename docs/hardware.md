# Hardware and controls

## DigiKey bill of materials

The November 2026 DigiKey order acknowledgement lists these five parts. Quantities are quantities ordered.

| Part | Manufacturer and model | Qty | DigiKey SKU | Role |
| --- | --- | ---: | --- | --- |
| Servo controller | Kitronik Movement Module 2177 | 1 | [1927-2177-ND](https://www.digikey.com/en/products/detail/kitronik-ltd/2177/18093076) | Drives the servo and sets travel. Powered by 5 V through Micro-USB. |
| Project box | Hammond Manufacturing 1591LSBK | 1 | [HM100-ND](https://www.digikey.com/en/products/detail/hammond-manufacturing/1591LSBK/130860) | Black plastic enclosure for the desk controller. Approximately 85 × 56 mm externally in plan. |
| Pushbutton | Same Sky PB4-M-BK-D-67 | 1 | [2223-PB4-M-BK-D-67-ND](https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/PB4-M-BK-D-67/28949222) | Optional remote switch. Normally open, momentary, with a 12 mm panel cutout. |
| Servo extension | Adafruit 973 | 3 | [1528-1171-ND](https://www.digikey.com/en/products/detail/adafruit-industries-llc/973/5353631) | Three-wire extension between the desk controller and camera. Each cable is 19.5 in (about 0.5 m). |
| Servo | DFRobot SER0049 | 1 | [1738-SER0049-ND](https://www.digikey.com/en/products/detail/dfrobot/SER0049/13280116) | 9 g positional clutch servo with nominal 180° travel and a rated supply of 4.8–6 V DC. V7 uses measurements of this servo and its stock horn. |

## Connections

- Supply 5 V through the controller's Micro-USB connector. The USB cable and power supply were outside this order.
- Run the servo lead to the controller through the extension cables as needed. Match the signal, power, and ground positions on the controller header to the connector.
- Use the controller's onboard button or wire the panel-mounted momentary button in parallel with it. The extra button is optional if the onboard button is accessible.
- Set the travel with the controller's trimmer. V7 models a 135° opening. Check the servo travel before coupling it to the cap, then check that the assembled cap clears the lens at both endpoints.

See the [Kitronik 2177 datasheet](https://core-electronics.com.au/attachments/localcontent/2177-kitronik-movement-module-datsheet_293269fda8a.pdf) for the board connections and the [DFRobot servo specifications](https://www.dfrobot.com/product-2120.html/) for the servo.
