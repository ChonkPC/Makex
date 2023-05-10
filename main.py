import argparse
import os
from pathlib import Path
from rich import print
from rich.console import Console
from rich.syntax import Syntax

console = Console()

# Builder
class Builder:
  def __init__(
    self,
    path: str
  ):
    self.path = path

  def build_base(self):
    pass 

  def create_data_table(self, config):
    path = os.path.join(
      self.path,
      "DATA"
    )

    data_points = {}
    current_addr = config["DATA_AD"]
    total_len = 0
    total_size = 0

    for entity in os.listdir(path = path):
      print("-----------------------")
      print(f"Found entity -> \"{entity}\"")

      # Construct data

      # We need to calculate the size, so first
      # just read the entity data
      with open(
        os.path.join(
          path,
          entity
        ),
        "rb"
      ) as f:
        data = f.read()

      #  bytes.__len__ is the size of the bytes
      size = len(data)
      total_size += size

      name = entity.encode("ascii") 
      if len(name) <= 10:
        bytes_name = name + b"\0"*(0xA - len(entity.encode("ascii")))
      else:
        print(f"[bold red]Entity name was too long \"{entity}\"[/bold red]")
        quit(1)

      entity_data = [
        *bytes_name,
        *current_addr.to_bytes(4, "big"),
        *size.to_bytes(4, "big"),
      ]

      total_len += len(bytearray(entity_data))

      if total_len > 0x1C2:
        raise Exception("Too many entities, exceeded table capacity")

      data_points[entity] = entity_data
      print(f"Loaded entity \[\"{entity}\"] - Size: {hex(size)} Addr: {hex(current_addr)}")

      current_addr += size

    print("-----------------------")
    print(f"Table size: {hex(total_len)}")
    # Pad
    padding = 0x1C2 - total_len

    data_points["padding"] = [*[0]*padding]
    data_points["_size"] = [total_size]

    return data_points

  def run(self):
    entities: list[str] = []
    for entity in os.listdir(path = self.path):
      entities.append(entity)

    if sorted(entities) != sorted(["CODE", "CONF", "DATA"]):
      print("[bold red]Invalid format. Entries not matched, make sure to follow the standard provided[/bold red]")
      quit(1)

    # The entries match
    # Now we read the config
    with open(
      os.path.join(
        self.path,
        "CONF"
      )
    ) as file:
      config_lines = file.readlines()

    # Process config
    config = {}
    for line in config_lines:
      if line:
        l = line.split("=")
        config[l[0]] = int(l[1], 16)
    
    if not all(k in config for k in ("CODE_AD","DATA_AD")):
      print("[bold red]Invalid format. Config incomplete, make sure to follow the standard provided[/bold red]")
      quit(1)
    
    magic = ".EXE".encode("ascii")

    into_bytes = lambda num: (hex(num >> 8), hex(num & 0xFF))

    data_table = self.create_data_table(config)

    with open(
      os.path.join(
        self.path,
        "CODE"
      ),
      "rb"
    ) as f:
      code_lines = f.readlines()

    final = [
      *magic,
      *[0]*12,
      *config["CODE_AD"].to_bytes(4, "big"),
      *len(bytearray(b''.join(code_lines))).to_bytes(4, "big"),
      *[0]*8,
      *config["DATA_AD"].to_bytes(4, "big"),
      *data_table["_size"][0].to_bytes(4, "big"),
      *[0]*216,
      #*[int(_, 16) for _ in into_bytes(config["CODE_AD"])
    ]

    print(f"""\
CODE_AD: {hex(config["CODE_AD"])}
CODE_SZ: {hex(len(bytearray(b''.join(code_lines))))}
DATA_AD: {hex(config["DATA_AD"])}
DATA_SZ: {hex(data_table["_size"][0])}""")

    # Add data table
    for ent in data_table:
      for _ in data_table[ent]:
        if ent[0] != '_':
          final.append(_)

    # Add more padding
    final += [*[0]*0x3E]

    # Add CODE binary
    for l in code_lines:
      final += l

    try:
      with open("out", "wb+") as f:
        f.write(bytearray(final))
    except ValueError:
      print("[red bold]Failed to convert final to bytearray[/red bold]")
      print(final)
      quit(1)

    except TypeError:
      print("[red bold]Failed to convert final to bytearray. Something was of the wrong type[/red bold]")
      print(final)
      quit(1)

# Argument parsing
parser = argparse.ArgumentParser()

parser.add_argument("path")

if __name__ == "__main__":
  args = parser.parse_args()

  # Define our target directory
  target = Path(args.path)
  if not target.exists():
    print("[red bold]The target directory doesn't exist[/red bold]")
    exit(1)

  # Start the construction
  builder = Builder(
    path = args.path
  )

  builder.run()