# https://github.com/DenverCoder1/minimalistic-wallpaper-collection
# For loop bash script that downloads X amount of wallpapers from above github

echo "Enter number of random images to download: "
read picLimit

for i in $(seq 1 $picLimit);
do
    wget "https://minimalistic-wallpaper.demolab.com/?random=$i&redirect=1" -O $i.jpg
done