import yaml
import uvicorn


if __name__ == "__main__":
    stream = open("config.yaml", "r")
    cfg = yaml.load(stream, Loader=yaml.FullLoader)

    uvicorn.run("main:app",reload=True,port=cfg['port'], host=cfg['host'])