from ttls.client import Twinkly
import time
BLACK = (0x00,0x00,0x00)
RED = (0xFF,0x00,0x00)
GREEN = (0x00,0xFF,0x00)
DARK_GREEN = (0x00,0x77,0x00)

from awtrixfont import font_glyphs,font_data,font_height


class TwinklySquares(Twinkly):
    
    def __init__(self,host,rows=None,cols=None,layout=None,clock_x_offset=1,clock_y_offset=1,blink_speed=1000,mode="movie"):
        # Call the parent constructor
        super().__init__(host=host)
        self.clock_x_offset = clock_x_offset
        self.clock_y_offset = clock_y_offset
        self.blink_speed = blink_speed
        self.mode = mode
        self.blink = True
        # If layout is provided, just set it
        if layout is not None: 
            self.layout = layout
            self.rows = len(layout)
            self.cols = len(layout[0])
        elif (cols is not None) and (rows is not None):
            # If not layout is provided, start with the default based on number or rows and columns
            self.rows = rows
            self.cols = cols
            self.layout = list() 
            i = 0
            for r in range(rows):
                rr = list()
                for c in range(cols):
                    rr.append([i,0])
                    i+=1
                self.layout.append(rr)
        else:
            raise Exception("Either layout must be provided or cols and rows")

    def print_glyph(self,res,n,x_offset,y_offset):
        glyph_info = font_glyphs[n-0x20]
        y_offset += font_height + glyph_info[5]
        
        # Work through the font grid
        for y in range(glyph_info[2]):
            mask  = 0b10000000
            char = font_data[glyph_info[0]+y]
            for x in range(3):
                # If pixel should be lit
                if char & mask:
                    # Update the correct pixel
                    index = self.xyToIndex(x+x_offset,y+y_offset)
                    if index != -1:
                        res[index] = RED
                mask >>= 1    

        return glyph_info[3]

    def print_text(self,text,x_offset,y_offset,frame):
        # For each of the four digits
        for c in text:
            # Get the number
            x_offset += self.print_glyph(frame,ord(c),x_offset,y_offset)

    async def recalibrate(self):
        self.layout = list() 
        i = 0
        for r in range(self.rows):
            rr = list()
            for c in range(self.cols):
                rr.append([i,0])
                i+=1
            self.layout.append(rr)        
        await self.show_calibrate()

    async def calibrate_set_order(self,order):
        for r in range(self.rows):
            for c in range(self.cols):
                self.layout[r][c][0] = order[r][c]
        await self.show_calibrate()

    async def calibrate_rotate(self,index):
        self.layout[index//self.cols][index%self.cols][1] = (self.layout[index//self.cols][index%self.cols][1]+1)%4
        await self.show_calibrate()

    async def render_full_frame(self):
        frame = [BLACK] * self.length
        self.render_statuses(frame)
        self.render_temperatures(frame,0,10)
        frame = self.render_clock(frame,self.clock_x_offset,self.clock_y_offset)

        if self.mode == "movie":
            await self.send_movie(frame,2)
        elif self.mode == "rt":
            await self.send_rt(frame)

    def render_statuses(self,frame):
        for i in range(2,21,3):
            j=7
            frame[self.xyToIndex(i,j)] = DARK_GREEN
            frame[self.xyToIndex(i,j+1)] = DARK_GREEN
            frame[self.xyToIndex(i+1,j)] = DARK_GREEN
            frame[self.xyToIndex(i+1,j+1)] = DARK_GREEN


    def render_clock(self,frame,x_offset,y_offset):
        # Render
        if self.mode == "movie":
            numbers = time.strftime("%H %M",time.localtime())     
            self.print_text(numbers,x_offset,y_offset,frame)
            frame *= 2
            numbers = time.strftime("%H:%M",time.localtime())
            self.print_text(numbers,x_offset,y_offset,frame)
        else:
            self.blink = not self.blink
            if self.blink:
                numbers = time.strftime("%H:%M",time.localtime())
            else:
                numbers = time.strftime("%H %M",time.localtime())            
            self.print_text(numbers,x_offset,y_offset,frame)

        return frame

    def render_temperatures(self,frame,x_offset,y_offset):
        # Convert current time to four separate digits
        temps = [-23,-56]
        numbers = "-23-45"

        # For each of the four digits and 2 minus signs
        self.print_text(numbers,x_offset,y_offset,frame)
                

    async def show_calibrate(self):
        frame = [BLACK] * self.length
        i = 0
        for r in range(self.rows):
            for c in range(self.cols):
                self.print_glyph(frame,i,c*8,r*8)
                frame[self.xyToIndex((c+1)*8-1,(r+1)*8-1)] = GREEN
                i+=1
        await self.send_movie(frame)

    async def send_movie(self,frame,frames_number=1):
        # Avoid flashing by first switching away from movie and then later back again
        await self.set_mode("rt")
        await self.set_movie_config(
            {
                "frames_number": frames_number,
                "loop_type": 0,
                "frame_delay": self.blink_speed,
                "leds_number": self.length,
            }
        )
        await self.upload_movie(bytes([item for t in frame for item in t]))
        await self.set_mode("movie")


    async def send_rt(self,frame):
        # Avoid flashing by first switching away from movie and then later back again
        await self.set_mode("rt")
        await self.send_frame_3(frame)

    def xyToIndex(self,x,y):
        if y < 0 or x < 0 or y//8 >= self.rows or x//8 >= self.cols:
            return -1
        # Determine which tile the requested global coordinate is on
        tile_info = self.layout[y//8][x//8]
        # Start with the base offset to end up on the right tile
        index = tile_info[0] * 64
        # Convert global coordinate to local coordinate on the tile
        x = x % 8
        y = y % 8
        # Depending on the tile orientation compute the correct local index
        # and add it to the global index
        if tile_info[1] == 0:
            if y % 2 == 0: 
                index += (7-y) * 8 + (7-x)
            else:
                index += (7-y) * 8 + x
        elif tile_info[1] == 1:
            if y % 2 == 0: 
                index += (y) * 8 + (7-x)
            else:
                index += (y) * 8 + x
        elif tile_info[1] == 2:
            if x % 2 == 0:
                index += (x) * 8 + (7-y) 
            else:
                index += (x) * 8 + y
        elif tile_info[1] == 3:
            if x % 2 == 0:
                index += (7-x) * 8 + (y)
            else:      
                index += (7-x) * 8 + (7-y)
               
        return index    
    
    def wait(self):
        if self.mode == "movie":
            time.sleep(60-time.localtime().tm_sec)
        if self.mode == "rt":
            time.sleep(self.blink_speed/1000)