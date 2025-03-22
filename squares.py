from ttls.client import Twinkly
BLACK = (0x00,0x00,0x00)
RED = (0xFF,0x00,0x00)
GREEN = (0x00,0xFF,0x00)

from small import digits,font_width,font_height,x_offsets,y_offset,colon_x_offset,colon_y_offset

class TwinklySquares(Twinkly):
    
    def __init__(self,host,rows=None,cols=None,layout=None):
        # Call the parent constructor
        super().__init__(host=host)
        
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
        # Work through the font grid
        for y in range(font_height):
            for x in range(font_width):
                # If pixel should be lit
                if digits[n][y][x] == 1:
                    # Update the correct pixel
                    res[self.xyToIndex(x+x_offset,y+y_offset)] = RED  

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

    async def show_calibrate(self):
        frame = [BLACK] * self.length
        i = 0
        for r in range(self.rows):
            for c in range(self.cols):
                self.print_glyph(frame,i,c*8,r*8)
                frame[self.xyToIndex((c+1)*8-1,(r+1)*8-1)] = GREEN
                i+=1
        await self.set_mode("rt")
        await self.set_movie_config(
            {
                "frames_number": 1,
                "loop_type": 0,
                "frame_delay": 1,
                "leds_number": self.length,
            }
        )
        await self.upload_movie(bytes([item for t in frame for item in t]))
        await self.set_mode("movie")

    
    def xyToIndex(self,x,y):
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