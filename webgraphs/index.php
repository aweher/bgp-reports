<?php
require_once 'common.php';
//header("Location: graph.php$dataset_qs");
?>

<html>
<head>
</head>
<body>
	<h1> IXP Reports </h1>
        <?php
            $dirs = array_filter(glob('data/*'), 'is_dir');
            foreach ($dirs as $dir){
        ?>        
	<a href="graph.php?dataset=<?php echo substr($dir, 5) ?>"><?php echo substr($dir, 5) ?></a><br />
        <?php } ?>
</body>
</html>
