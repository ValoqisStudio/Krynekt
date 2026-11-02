# usage: mix.sh video_with_sfx.mp4 voice.mp3 out.mp4
ffmpeg -y -loglevel error -i "$1" -i "$2" -filter_complex "\
[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,highpass=f=70,equalizer=f=200:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.2:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=4dB,asplit=2[v][vsc];\
[0:a]aresample=44100,volume=0.55[s];\
[s][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=10:release=300[sd];\
[v][sd]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.2:LRA=9[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 44100 -movflags +faststart "$3"
